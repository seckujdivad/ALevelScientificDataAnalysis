import math

import sciplot.datatable


class FitLines:
    """
    Object that holds plot data and outputs lines of best and worst fit

    Args:
        datatable (Datatable): a datatable with exactly two columns that has already had .load called on it
    """
    def __init__(self, datatable: sciplot.datatable.Datatable):
        self._datatable = datatable

        if len(self._datatable.as_columns()) != 2:
            raise ValueError("Datatable must have exactly 2 columns, not {}".format(len(self._datatable.as_columns())))
        
        #line with best gradient
        self.fit_best_gradient = None
        self.fit_best_intercept = None

        #line with min gradient
        self.fit_worst_min_gradient = None
        self.fit_worst_min_intercept = None

        #line with max gradient
        self.fit_worst_max_gradient = None
        self.fit_worst_max_intercept = None
    
    def calculate_all(self):
        self.calculate_best_fit()
        self.calculate_worst_fits()

    def calculate_best_fit(self): #https://www.dummies.com/education/math/statistics/how-to-calculate-a-regression-line/
        #get raw values
        x_values = [value.value for value in self._datatable.as_columns()[0]]
        y_values = [value.value for value in self._datatable.as_columns()[1]]

        #calculate means of x and y
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)

        #calculate diffsquares and diffs
        diffsquare_x = sum([pow(value - x_mean, 2) for value in x_values])
        diffsquare_y = sum([pow(value - y_mean, 2) for value in y_values])

        #calculate standard deviations
        stdev_x = math.sqrt(diffsquare_x / (len(x_values) - 1))
        stdev_y = math.sqrt(diffsquare_y / (len(y_values) - 1))

        #calculate sample pearson correlation coefficient https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
        correl = sum([(x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(len(x_values))]) / (math.sqrt(diffsquare_x) * math.sqrt(diffsquare_y))

        self.fit_best_gradient = correl * (stdev_y / stdev_x)
        self.fit_best_intercept = y_mean - (x_mean * self.fit_best_gradient)

    def calculate_worst_fits(self):
        pass

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