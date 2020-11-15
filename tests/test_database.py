import unittest
import sys
import os

up1 = os.path.abspath('../')
sys.path.insert(0, up1)

import sciplot.database as database #pylint: disable=import-error
import sciplot.datafile as datafile

sys.path.pop(0)


class TestDatabase(unittest.TestCase):
    def create_db(self):
        path = ''
        for path_to_test in [
            os.path.join(sys.path[0], 'datasets', 'database.db'),
            os.path.join(sys.path[0], 'tests', 'datasets', 'database.db')
        ]:
            if os.path.isfile(path_to_test):
                path = path_to_test
        
        if path == '':
            raise IOError("No valid path")

        return database.Database(path)

    def test_query(self):
        with self.create_db() as db:
            q = database.Query("SELECT * FROM TestTable", [], 0)
            db.query(q)
    
    def test_query_value_insertion(self):
        with self.create_db() as db:
            q = database.Query("SELECT * FROM TestTable WHERE TestTableID = (?)", [1], 0)
            db.query(q)

    def test_return_many(self):
        with self.create_db() as db:
            q = database.Query("SELECT * FROM TestTable WHERE Value = 1", [], 1)
            result = db.query(q)
            self.assertEqual(result, [[(1, 1, "Hello"), (2, 1, "World")]])
    
    def test_return_one(self):
        with self.create_db() as db:
            q = database.Query("SELECT * FROM TestTable WHERE TestTableID = 1", [], 2)
            result = db.query(q)
            self.assertEqual(result, [(1, 1, "Hello")])
    
    def test_write(self):
        with self.create_db() as db:
            q1 = database.Query('INSERT INTO TestTable ("Value", "String") VALUES (55, "Hello World!");', [], 0)
            q2 = database.Query('SELECT "Value", "String" FROM TestTable WHERE "Value" = 55;', [], 1)
            q3 = database.Query('ROLLBACK;', [], 0)
            result = db.query([q1, q2, q3])
            self.assertEqual(result, [[(55, "Hello World!")]])
    
    def test_multiline(self):
        with self.create_db() as db:
            query = database.Query('''
            INSERT INTO TestTable ("Value", "String") VALUES (55, "Hello World!");
            SELECT "Value", "String" FROM TestTable WHERE "Value" = 55;
            ROLLBACK;''', [], 1)
            self.assertEqual(db.query(query), [[], [(55, "Hello World!")], []])
    
    def test_bad_query(self):
        with self.create_db() as db:
            query = database.Query('SELECT BadColumn FROM InvalidTableName', [], 1)
            try:
                db.query(query)

                #this shouldn't pass
                raise Exception('The appropriate exception was not thrown')
            
            except database.sqlite3.OperationalError:
                pass #appropriate error raised, test passed


class TestDataFile(unittest.TestCase):
    def connect_datafile(self):
        path = ''
        for path_to_test in [
            os.path.join(sys.path[0], 'datasets', 'datafile.db'),
            os.path.join(sys.path[0], 'tests', 'datasets', 'datafile.db')
        ]:
            if os.path.isfile(path_to_test):
                path = path_to_test
        
        if path == '':
            raise IOError("No valid path")
        
        return datafile.DataFile(path)

    def test_list_constants(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_constants(), [(3.141592653589793, 'pi'), (9.80665, 'g'), (2.718281828459045, 'e')])
    
    def test_rollbacks(self):
        df = self.connect_datafile()
        query = database.Query("INSERT INTO Constant (UnitCompositeID, Value, Symbol) VALUES ((?), (?), (?))", [0, 32, "test"], 0)
        df.query(query)
        df.goto_rollback()
        self.test_list_constants()
        df.close()
    
    def test_add_constant(self):
        with self.connect_datafile() as df:
            primary_key = df.create_constant("test unit", 0.1, 0)
            self.assertEqual(df.get_constant_by_id(primary_key), ("test unit", 0.1, 0))
            df.goto_rollback()
    
    def test_list_si_units(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_base_units(), [(1, 's'), (2, 'm'), (3, 'kg'), (4, 'A'), (5, 'K'), (6, 'mol'), (7, 'cd')])
    
    def test_get_si_unit(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_base_unit(1), 's')
    
    def test_get_unit_by_id(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_unit_by_id(1), ('N', [(1, -2.0), (2, 1.0), (3, 1.0)]))
    
    def test_create_unit(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_unit_by_id(df.create_unit('test unit', [(1, -1), (2, 1)])), ('test unit', [(1, -1.0), (2, 1.0)]))
            df.goto_rollback()
    
    def test_list_units(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_units(), [1, 2, 3, 4, 5, 6])
    
    def test_get_metadata(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_metadata('name'), 'Young Modulus example dataset')
    
    def test_set_metadata(self):
        with self.connect_datafile() as df:
            df.set_metadata('test key', 'test value')
            self.assertEqual(df.get_metadata('test key'), 'test value')
            df.goto_rollback()
    
    def test_list_data_sets(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_data_sets(), [1, 2, 3, 4])
    
    def test_get_data_set(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_data_set(1), (4, 0.001, 0))
    
    def test_create_data_set(self):
        with self.connect_datafile() as df:
            primary_key = df.create_data_set(0.01, False, 1)
            self.assertEqual(df.get_data_set(primary_key), (1, 0.01, 0))
            df.goto_rollback()
    
    def test_remove_data_set(self):
        with self.connect_datafile() as df:
            df.remove_data_set(1)
            self.assertEqual(df.list_data_sets(), [2, 3, 4])
            df.goto_rollback()
    
    def test_get_data_points(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_data_points(1), [(i, 1.217) for i in range(1, 26, 1)])
    
    def test_remove_data_point(self):
        with self.connect_datafile() as df:
            df.remove_data_point(1)
            self.assertEqual(df.get_data_points(1), [(i, 1.217) for i in range(2, 26, 1)])
            df.goto_rollback()
    
    def test_create_data_point(self):
        with self.connect_datafile() as df:
            primary_key = df.create_data_point(12.345, 1)
            self.assertEqual(df.get_data_points(1), [(i, 1.217) for i in range(1, 26, 1)] + [(primary_key, 12.345)])
            df.goto_rollback()
    
    def test_get_data_point(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_data_point(1), (1, 1.217))
    
    def test_list_formulae(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_formulae(), [1, 2, 3, 4, 5])
    
    def test_get_formula(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.get_formula(1), '{l1}-{l0}')

    def test_create_formula(self):
        with self.connect_datafile() as df:
            primary_key = df.create_formula('{g}^2')
            self.assertEqual(df.get_formula(primary_key), '{g}^2')
            df.goto_rollback()

    def test_remove_formula(self):
        with self.connect_datafile() as df:
            df.remove_formula(1)
            self.assertNotIn(1, df.list_formulae())
            df.goto_rollback()
    
    def test_list_tables(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_tables(), [(1, 'Force-extension'), (2, 'Stress-strain')])

    def test_create_table(self):
        with self.connect_datafile() as df:
            primary_key = df.create_table('Test table')
            self.assertIn((primary_key, 'Test table'), df.list_tables())
            df.goto_rollback()

    def test_remove_table(self):
        with self.connect_datafile() as df:
            df.remove_table(1)
            self.assertNotIn((1, 'Force-extension'), df.list_tables())
            df.goto_rollback()
    
    def test_list_table_columns(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_table_columns(1), [(1, '00.000'), (7, '000.0')])
    
    def test_create_table_column(self):
        with self.connect_datafile() as df:
            df.create_table_column(1, 2, '0.0')
            self.assertIn((2, '0.0'), df.list_table_columns(1))
            df.goto_rollback()
    
    def test_remove_table_column(self):
        with self.connect_datafile() as df:
            df.remove_table_column(1, 1)
            self.assertNotIn((1, '00.000'), df.list_table_columns(1))
            df.goto_rollback()
    
    def test_list_plots(self):
        with self.connect_datafile() as df:
            self.assertEqual(df.list_plots(), [1, 2])
    
    def test_create_plot(self):
        with self.connect_datafile() as df:
            primary_key = df.create_plot(1, 'test', 2, 'test 2', True)
            self.assertIn(primary_key, df.list_plots())
            df.goto_rollback()

    def test_remove_plot(self):
        with self.connect_datafile() as df:
            df.remove_plot(1)
            self.assertNotIn(1, df.list_plots())
            df.goto_rollback()
    
    def test_getunitid_partial_match(self):
        with self.connect_datafile() as db:
            self.assertEqual(db.get_unit_id_by_table([(1, 1)]), [])
    
    def test_getunitid_empty(self):
        with self.connect_datafile() as db:
            self.assertEqual(db.get_unit_id_by_table([]), [6])
    
    def test_getunitid_exact_match(self):
        with self.connect_datafile() as db:
            self.assertEqual(db.get_unit_id_by_table([(1, -2), (2, 1), (3, 1)]), [1])
    
    def test_renameunit(self):
        with self.connect_datafile() as db:
            db.create_rollback()
            db.rename_unit(1, "renamed")

            self.assertEqual(db.get_unit_id_by_symbol("renamed"), [1])

            db.goto_rollback()
    
    def test_updateunit(self):
        with self.connect_datafile() as db:
            db.create_rollback()

            db.update_unit(1, [(1, -1), (3, 2)])
            self.assertEqual(set(db.get_unit_by_id(1)[1]), set([(1, -1), (3, 2)]))

            db.goto_rollback()

if __name__ == '__main__':
    unittest.main()