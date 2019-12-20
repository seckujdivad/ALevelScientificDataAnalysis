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