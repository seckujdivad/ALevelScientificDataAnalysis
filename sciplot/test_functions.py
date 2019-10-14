import unittest

import functions


class TestFunction(unittest.TestCase):
    def asserter(self, string, value, message = '', args = {}):
        return self.assertEqual(functions.Function(string).evaluate(args), value, message)

    def test_addition(self):
        self.asserter('9+3', 9 + 3)
        self.asserter('111+1024', 111 + 1024)
    
    def test_addition_multiple(self):
        self.asserter('3+10+4', 3 + 10 + 4)
        self.asserter('1+2+3+4+321', 1 + 2 + 3 + 4 + 321)
    
    def test_with_spaces(self):
        self.asserter('1 + 2', 1 + 2)
        self.asserter('3 - 5', 3 - 5)
    
    def test_subtraction(self):
        self.asserter('10-5', 10 - 5)
    
    def test_bidmas(self):
        self.asserter('3-5*3', 3 - (5 * 3))
        self.asserter('(3-5)*3', (3 - 5) * 3)
    
    def test_indices(self):
        self.asserter('4^2', 4 * 4)
        self.asserter('4^0.5', 2)
    
    def test_functions(self):
        self.asserter('sin0', 0)
        self.asserter('cos0', 1)
        self.asserter('2cos0', 2)
    
    def test_variables(self):
        self.asserter('2*{x}', 6, args = {'x': 3})


if __name__ == '__main__':
    unittest.main()