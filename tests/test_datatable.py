import unittest
import sys
import os

up1 = os.path.abspath('../')
sys.path.insert(0, up1)

import sciplot.datatable
import sciplot.datafile
import sciplot.functions

sys.path.pop(0)


class TestDatatable(unittest.TestCase):
    def create_datafile(self):
        path = ''
        for path_to_test in [
            os.path.join(sys.path[0], 'datasets', 'datafile.db'),
            os.path.join(sys.path[0], 'tests', 'datasets', 'datafile.db')
        ]:
            if os.path.isfile(path_to_test):
                path = path_to_test
        
        if path == '':
            raise IOError("No valid path")
        
        return sciplot.datafile.DataFile(path)

    def create_datatable(self, datafile):
        return sciplot.datatable.Datatable(datafile)
    
    def test_load_noerrors(self):
        with self.create_datafile() as datafile:
            datatable = self.create_datatable(datafile)
            datatable.set_variables([2, 4])
            datatable.load(self.generic_datatable)
    
    generic_datatable = {'pi': sciplot.functions.Value(3.14159265359, 0.00, False, []),
                         'g': sciplot.functions.Value(9.81, 0.01, False, [(1, 1), (2, 1), (3, -2)])}