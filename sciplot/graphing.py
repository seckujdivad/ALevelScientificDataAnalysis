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

    def calculate_best_fit(self):
        pass

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