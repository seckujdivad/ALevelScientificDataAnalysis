import unittest
import sys
import os

up1 = os.path.abspath('../')
sys.path.insert(0, up1)

import sciplot.units as units #pylint: disable=import-error
import sciplot.database as database #pylint: disable=import-error

sys.path.pop(0)


class TestUnits(unittest.TestCase):
    def create_db(self):
        return database.DataFile(os.path.join(sys.path[0], 'datasets', 'datafile.db'))

    def test_getcompositeid_partial_match(self):
        with self.create_db() as db:
            self.assertEqual(units.get_composite_id(db, [(1, 1)]), -1)
    
    def test_getcompositeid_empty(self):
        with self.create_db() as db:
            self.assertEqual(units.get_composite_id(db, []), -1)
    
    def test_getcompositeid_exact_match(self):
        with self.create_db() as db:
            self.assertEqual(units.get_composite_id(db, [(1, -2), (2, 1), (3, 1)]), 1)
    
    def test_createcomposite_create(self):
        with self.create_db() as db:
            db.create_rollback()

            unit_table = [(3, -1), (2, 3)]
            primary_key = units.create_composite(db, "Hello world!", unit_table)
            self.assertEqual(primary_key, units.get_composite_id(db, unit_table))

            db.goto_rollback()
    
    def test_getunit(self):
        with self.create_db() as db:
            self.assertEqual(units.get_unit(db, 6), "mol")
    
    def test_getunitid(self):
        with self.create_db() as db:
            self.assertEqual(units.get_unit_id(db, "mol"), 6)


if __name__ == '__main__':
    unittest.main()