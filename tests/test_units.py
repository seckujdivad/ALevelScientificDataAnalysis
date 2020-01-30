import unittest
import sys
import os

up1 = os.path.abspath('../')
sys.path.insert(0, up1)

import sciplot.units as units #pylint: disable=import-error
import sciplot.database as database #pylint: disable=import-error

sys.path.pop(0)


class TestGetCompositeID(unittest.TestCase):
    def create_db(self):
        return database.Database(os.path.join(sys.path[0], 'datasets', 'datafile.db'))

    def test_partial_match(self):
        with self.create_db() as db:
            self.assertEqual(units.get_composite_id(db, [(1, 1)]), -1)


if __name__ == '__main__':
    unittest.main()