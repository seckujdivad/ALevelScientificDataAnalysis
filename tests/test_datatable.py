import unittest
import sys
import os

up1 = os.path.abspath('../')
sys.path.insert(0, up1)

import sciplot.datatable
import sciplot.datafile

sys.path.pop(0)


class TestDatatable(unittest.TestCase):
    def create_datafile(self):
        return sciplot.datafile.DataFile(os.path.join(sys.path[0], 'datasets', 'datafile.db'))

    def create_datatable(self, datafile):
        return sciplot.datatable.Datatable(datafile)
    
    def test_load(self):
        with self.create_datafile() as datafile:
            datatable = self.create_datatable(datafile)
            datatable.set_variables([1, 2])
            datatable.load({})