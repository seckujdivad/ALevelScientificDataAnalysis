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
        return sciplot.datafile.DataFile(os.path.join(sys.path[0], 'datasets', 'datafile.db'))

    def create_datatable(self, datafile):
        return sciplot.datatable.Datatable(datafile)
    
    def test_load_noerrors(self):
        with self.create_datafile() as datafile:
            datatable = self.create_datatable(datafile)
            datatable.set_variables([2, 4])
            datatable.load(self.generic_datatable)
    
    generic_datatable = {'g': sciplot.functions.Value(9.81, 0.01, False, [(1, 1), (2, 1), (3, -2)]),
                         'volume': sciplot.functions.Value(532, 0.1, True, [(2, 3)]),
                         'mass': sciplot.functions.Value(25, 1, False, [(1, 1)])}