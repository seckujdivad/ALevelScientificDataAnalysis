import unittest

import database #pylint: disable=import-error


class TestDatabase(unittest.TestCase):
    def test_query(self):
        db = database.Database('../resources/test datasets/database.db')
        q = database.Query("SELECT * FROM TestTable", [], 0)
        db.query(q)
        db.close()
    
    def test_insertion(self):
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