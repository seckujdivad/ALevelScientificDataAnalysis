import unittest
import math

import functions #pylint: disable=import-error


class TestFunction(unittest.TestCase):
    def asserter(self, string, value, message = '', args = {}):
        return self.assertEqual(functions.Function(string).evaluate(args).value, value, message)

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
    
    def test_multiplication(self):
        self.asserter('5*10', 5 * 10)
        self.asserter('5*0.5', 2.5)
    
    def test_division(self):
        self.asserter('12/3', 4)
        self.asserter('5/0.5', 10)
    
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
        self.asserter('abs(-1)', 1)
        self.asserter('log(100)', 2)
        self.asserter('ln({})'.format(math.e), 1)
    
    def test_variables(self):
        self.asserter('2*{x}', 6, args = self.convert_datatable({'x': 3}))
    
    def test_pre_eval_keeps_result(self):
        expr = '1 + (3 * 2 * {g}) + {k}'
        constants = self.convert_datatable({'g': 9.81})
        datatable = self.convert_datatable({'k': 50})
        datatable.update(constants)
        default = functions.Function(expr)
        optimised = functions.Function(expr)
        optimised.pre_evaluate(constants)
        self.assertEqual(default.evaluate(datatable).value, optimised.evaluate(datatable).value)
    
    def test_pre_eval_reduces_complexity(self):
        expr = '1 + (3 * 2 * {g}) + {k}'
        constants = self.convert_datatable({'g': 9.81})
        datatable = self.convert_datatable({'k': 50})
        datatable.update(constants)
        default = functions.Function(expr)
        optimised = functions.Function(expr)
        optimised.pre_evaluate(constants)
        self.assertLess(optimised.num_nodes(), default.num_nodes())
    
    def convert_datatable(self, datatable): #convert to new style
        result = {}
        for key in datatable:
            result[key] = functions.Value(datatable[key])
        return result


if __name__ == '__main__':
    unittest.main()