import math
import typing


class FitLines:
    """
    Object that holds plot data and outputs lines of best and worst fit

    Args:
        datatable (Datatable): a datatable with exactly two columns that has already had .load called on it
    """
    def __init__(self, datatable):
        self._datatable = datatable

        if len(self._datatable.as_columns()) != 2:
            raise ValueError("Datatable must have exactly 2 columns, not {}".format(len(self._datatable.as_columns())))
        
        #line with best gradient
        self.fit_best_gradient = None
        self.fit_best_intercept = None

        #line with max gradient
        self.fit_worst_max_gradient = None
        self.fit_worst_max_intercept = None

        #line with min gradient
        self.fit_worst_min_gradient = None
        self.fit_worst_min_intercept = None
    
    def calculate_all(self):
        self.calculate_best_fit()
        self.calculate_worst_fits()

    def calculate_best_fit(self): #https://www.dummies.com/education/math/statistics/how-to-calculate-a-regression-line/
        #get raw values
        x_values = [value.value for value in self._datatable.as_columns()[0]]
        y_values = [value.value for value in self._datatable.as_columns()[1]]

        if len(x_values) != len(y_values):
            raise ValueError("The data to calculate a fit line for has uneven length: x = {}, y = {}".format(len(x_values), len(y_values)))
        
        if len(x_values) < 2:
            raise ValueError("At least two value pairs are needed to calculate a fit line (only {} pair(s) exist)".format(len(x_values)))

        #calculate means of x and y
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)

        #calculate diffsquares and diffs
        diffsquare_x = sum([pow(value - x_mean, 2) for value in x_values])
        diffsquare_y = sum([pow(value - y_mean, 2) for value in y_values])

        if diffsquare_x == 0:
            raise ValueError("Can\'t calculate a fit line for data where all x values are the same")

        if diffsquare_y == 0:
            raise ValueError("Can\'t calculate a fit line for data where all y values are the same")

        #calculate standard deviations
        stdev_x = math.sqrt(diffsquare_x / (len(x_values) - 1))
        stdev_y = math.sqrt(diffsquare_y / (len(y_values) - 1))

        #calculate sample pearson correlation coefficient https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
        correl = sum([(x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(len(x_values))]) / (math.sqrt(diffsquare_x) * math.sqrt(diffsquare_y))

        self.fit_best_gradient = correl * (stdev_y / stdev_x)
        self.fit_best_intercept = y_mean - (x_mean * self.fit_best_gradient)

    def calculate_worst_fits(self):
        x_values, y_values = self._datatable.as_columns()

        potential_fit_lines: typing.List[typing.Tuple[float, float]] = []

        for switch in [(a, b, c, d) for a in [1, -1] for b in [1, -1] for c in [1, -1] for d in [1, -1]]: #compute cartesian product
            for i in range(len(x_values)):
                for j in range(len(x_values)):
                    if i != j:
                        first_value_x = x_values[i]
                        first_value_y = y_values[i]
                        second_value_x = x_values[j]
                        second_value_y = y_values[j]

                        point_first = [first_value_x.value + (switch[0] * first_value_x.absolute_uncertainty), first_value_y.value + (switch[1] * first_value_y.absolute_uncertainty)]
                        point_second = [second_value_x.value + (switch[2] * second_value_x.absolute_uncertainty), second_value_y.value + (switch[3] * second_value_y.absolute_uncertainty)]
                        gradient = (point_second[1] - point_first[1]) / (point_second[0] - point_first[0])
                        intercept = point_first[1] - (point_first[0] * gradient)
                        
                        if self._check_line(gradient, intercept, x_values, y_values):
                            potential_fit_lines.append((gradient, intercept))
        
        if len(potential_fit_lines) == 0:
            self.fit_worst_max_gradient = None
            self.fit_worst_max_intercept = None
            self.fit_worst_min_gradient = None
            self.fit_worst_min_intercept = None

        else:
            max_index = 0
            min_index = 0
            for i in range(len(potential_fit_lines)):
                if potential_fit_lines[i][0] > potential_fit_lines[max_index][0]:
                    max_index = i
                if potential_fit_lines[i][0] < potential_fit_lines[min_index][0]:
                    min_index = i
            
            self.fit_worst_max_gradient, self.fit_worst_max_intercept = potential_fit_lines[max_index]
            self.fit_worst_min_gradient, self.fit_worst_min_intercept = potential_fit_lines[min_index]

    def _check_line(self, gradient, intercept, x_values, y_values):
        for i in range(len(x_values)):
            if not self._line_covers_value(gradient, intercept, x_values[i], y_values[i]):
                return False
        return True

    def _line_covers_value(self, gradient, intercept, x_value, y_value):
        return self._line_covers_value_axes(gradient, intercept, x_value, y_value) or self._line_covers_value_axes(gradient, intercept, y_value, x_value)
    
    def _line_covers_value_axes(self, gradient, intercept, x_value, y_value):
        min_x = x_value.value - x_value.absolute_uncertainty
        max_x = x_value.value + x_value.absolute_uncertainty
        min_y = y_value.value - y_value.absolute_uncertainty
        max_y = y_value.value + y_value.absolute_uncertainty

        touches_min_x = min_y <= (intercept + (gradient * min_x)) <= max_y
        touches_max_x = min_y <= (intercept + (gradient * max_x)) <= max_y

        return touches_min_x or touches_max_x

    #worst fit properties
    def _get_fit_worst_gradient(self):
        if None in [self.fit_best_gradient, self.fit_worst_max_gradient, self.fit_worst_min_gradient]:
            raise RuntimeError('You must call calculate before accessing this value')
        else:
            if self.fit_worst_max_gradient - self.fit_best_gradient > self.fit_best_gradient - self.fit_worst_min_gradient:
                return self.fit_worst_max_gradient
            else:
                return self.fit_worst_min_gradient

    def _get_fit_worst_intercept(self):
        if None in [self.fit_best_gradient, self.fit_worst_max_gradient, self.fit_worst_min_gradient, self.fit_worst_max_intercept, self.fit_worst_min_intercept]:
            raise RuntimeError('You must call calculate before accessing this value')
        else:
            if self.fit_worst_max_gradient - self.fit_best_gradient > self.fit_best_gradient - self.fit_worst_min_gradient:
                return self.fit_worst_max_intercept
            else:
                return self.fit_worst_min_intercept

    fit_worst_gradient = property(_get_fit_worst_gradient)
    fit_worst_intercept = property(_get_fit_worst_gradient)