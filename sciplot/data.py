UNCERTAINTY_ABSOLUTE = "uncertainty absolute"
UNCERTAINTY_PERCENTAGE = "uncertainty percentage"

class Data:
    def __init__(self):
        self._data = []
        self._column_titles = []
    
    def new_column(self, title, uncertainty, uncertainty_type):
        """
        Adds a new data column

        Args:
            title (str): column title
            uncertainty (float): size of uncertainty on all data points in this column
            uncertainty_type (UNCERTAINTY_PERCENTAGE or UNCERTAINTY_ABSOLUTE): type of uncertainty
        """

        self._column_titles.append(title)
        for row in self._data:
            row.append(0)

    def new_row(self):
        pass

    def get_column(self, index):
        result = []
        for row in self._data:
            result.append(row[index])
        return result
    
    def get_column_by_title(self, index):
        return self.get_column(self._column_titles[index])
    
    def get_row(self, index):
        return self._data[index]