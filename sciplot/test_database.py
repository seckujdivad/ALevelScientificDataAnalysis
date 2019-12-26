import unittest

import database #pylint: disable=import-error


class TestDatabase(unittest.TestCase):
    def test_query(self):
        db = database.Database('../resources/test datasets/database.db')
        q = database.Query("SELECT * FROM TestTable", [], 0)
        db.query(q)
        db.close()
    
    def test_query_value_insertion(self):
        db = database.Database('../resources/test datasets/database.db')
        q = database.Query("SELECT * FROM TestTable WHERE TestTableID = (?)", [1], 0)
        db.query(q)
        db.close()

    def test_return_many(self):
        db = database.Database('../resources/test datasets/database.db')
        q = database.Query("SELECT * FROM TestTable WHERE Value = 1", [], 1)
        result = db.query(q)
        self.assertEqual(result, [[(1, 1, "Hello"), (2, 1, "World")]])
        db.close()
    
    def test_return_one(self):
        db = database.Database('../resources/test datasets/database.db')
        q = database.Query("SELECT * FROM TestTable WHERE TestTableID = 1", [], 2)
        result = db.query(q)
        self.assertEqual(result, [(1, 1, "Hello")])
        db.close()
    
    def test_write(self):
        db = database.Database('../resources/test datasets/database.db')
        q0 = database.Query('BEGIN;', [], 0)
        q1 = database.Query('INSERT INTO TestTable ("Value", "String") VALUES (55, "Hello World!");', [], 0)
        q2 = database.Query('SELECT "Value", "String" FROM TestTable WHERE "Value" = 55;', [], 1)
        q3 = database.Query('ROLLBACK;', [], 0)
        result = db.query([q0, q1, q2, q3])
        self.assertEqual(result, [[(55, "Hello World!")]])
        db.close()
    
    def test_multiline(self):
        db = database.Database('../resources/test datasets/database.db')
        query = database.Query('''BEGIN;
        INSERT INTO TestTable ("Value", "String") VALUES (55, "Hello World!");
        SELECT "Value", "String" FROM TestTable WHERE "Value" = 55;
        ROLLBACK;''', [], 1)
        self.assertEqual(db.query(query), [[], [], [(55, "Hello World!")], []])
        db.close()
    
    def test_bad_query(self):
        db = database.Database('../resources/test datasets/database.db')
        query = database.Query('SELECT BadColumn FROM InvalidTableName', [], 1)
        try:
            db.query(query)

            #this shouldn't pass
            raise Exception('The appropriate exception was not thrown')
        
        except database.sqlite3.OperationalError:
            pass #appropriate error raised, test passed

        finally:
            db.close()


class TestDataFile(unittest.TestCase):
    def connect_datafile(self):
        return database.DataFile('../resources/test datasets/datafile.db')

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
            self.assertEqual(df.list_units(), [1, 2, 3])