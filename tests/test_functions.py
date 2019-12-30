import unittest
import math
import sys
import os

up1 = os.path.abspath('../sciplot')
sys.path.insert(0, up1)

import functions #pylint: disable=import-error

sys.path.pop(0)


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
    
    def test_addition_uncertainty(self):
        func = functions.Function('{g} + {g}')
        result = func.evaluate(self.generic_datatable)
        self.assertEqual(result.absolute_uncertainty, 0.02)
    
    def test_addition_units(self):
        result = functions.Function('{g} + {g}').evaluate(self.generic_datatable).units
        result.sort()
        self.assertEqual(result, self.generic_datatable['g'].units)

    def test_subtraction_uncertainty(self):
        func = functions.Function('{g} - {mass}')
        result = func.evaluate(self.generic_datatable)
        self.assertEqual(result.absolute_uncertainty, 1.01)

    def test_subtraction_units(self):
        result = functions.Function('{g} - {g}').evaluate(self.generic_datatable).units
        result.sort()
        self.assertEqual(result, self.generic_datatable['g'].units)

    def test_multiplication_uncertainty(self):
        func = functions.Function('{g} * {mass}')
        result = func.evaluate(self.generic_datatable)
        self.assertEqual(result.percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty + self.generic_datatable['mass'].percentage_uncertainty)

    def test_multiplication_units(self):
        result = functions.Function('{g} * {g}').evaluate(self.generic_datatable).units
        result.sort()
        self.assertEqual(result, [(unit_id, power * 2) for unit_id, power in self.generic_datatable['g'].units])

    def test_division_uncertainty(self):
        func = functions.Function('{g} / {mass}')
        result = func.evaluate(self.generic_datatable)
        self.assertEqual(result.percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty + self.generic_datatable['mass'].percentage_uncertainty)

    def test_division_units(self):
        result = functions.Function('{g} / {g}').evaluate(self.generic_datatable).units
        self.assertEqual(result, [])

    def test_indices_uncertainty(self):
        func = functions.Function('{g}^2')
        result = func.evaluate(self.generic_datatable)
        self.assertEqual(result.percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty * 2)

    def test_indices_units(self):
        result = functions.Function('{g}^2').evaluate(self.generic_datatable).units
        result.sort()
        self.assertEqual(result, [(unit_id, power * 2) for unit_id, power in self.generic_datatable['g'].units])

    def test_misc_funcs_uncertainty(self):
        self.assertEqual(functions.Function('sin{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('cos{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('tan{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('arcsin({g} / 10)').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('arccos({g} / 10)').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('arctan({g} / 10)').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('rad{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('deg{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('abs{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('ln{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)
        self.assertEqual(functions.Function('log{g}').evaluate(self.generic_datatable).percentage_uncertainty, self.generic_datatable['g'].percentage_uncertainty)

    def test_misc_funcs_units(self):
        self.assertEqual(functions.Function('sin{g}').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('cos{g}').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('tan{g}').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('arcsin({g} / 10)').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('arccos({g} / 10)').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('arctan({g} / 10)').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('rad{g}').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('deg{g}').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('abs{g}').evaluate(self.generic_datatable).units, self.generic_datatable['g'].units)
        self.assertEqual(functions.Function('ln{g}').evaluate(self.generic_datatable).units, [])
        self.assertEqual(functions.Function('log{g}').evaluate(self.generic_datatable).units, [])
    
    def test_unopened_brackets(self):
        try:
            functions.Function('1)').evaluate({})
            raise Exception('An exception wasn\'t thrown when it should\'ve been')
        except ValueError: #appropriate exception was thrown
            pass

    def test_unclosed_brackets(self):
        try:
            functions.Function('(1').evaluate({})
            raise Exception('An exception wasn\'t thrown when it should\'ve been')
        except ValueError: #appropriate exception was thrown
            pass

    def test_unopened_variable(self):
        try:
            functions.Function('1}').evaluate({})
            raise Exception('An exception wasn\'t thrown when it should\'ve been')
        except ValueError: #appropriate exception was thrown
            pass

    def test_unclosed_variable(self):
        try:
            functions.Function('{1').evaluate({})
            raise Exception('An exception wasn\'t thrown when it should\'ve been')
        except ValueError: #appropriate exception was thrown
            pass

    def test_not_enough_values(self):
        try:
            functions.Function('+').evaluate({})
            raise Exception('An exception wasn\'t thrown when it should\'ve been')
        except ValueError: #appropriate exception was thrown
            pass

    def test_dependencies(self):
        self.assertEqual(functions.Function('{m}-{c}').evaluate_dependencies(), ['m', 'c'])
        self.assertEqual(functions.Function('({g}*{m})-{c}').evaluate_dependencies(), ['g', 'm', 'c'])

    generic_datatable = {'g': functions.Value(9.81, 0.01, False, [(1, 1), (2, 1), (3, -2)]),
                         'volume': functions.Value(532, 0.1, True, [(2, 3)]),
                         'mass': functions.Value(25, 1, False, [(1, 1)])}


class TestVariable(unittest.TestCase):
    def format_value(self, formatstring, value):
        return functions.Value(value).format(formatstring)

    def test_perctoabs(self):
        self.assertEqual(functions.Value(100, 0.1, True).absolute_uncertainty, 10)
    
    def test_abstoperc(self):
        self.assertEqual(functions.Value(100, 15, False).percentage_uncertainty, 0.15)
    
    def test_format_sigfig(self):
        self.assertEqual(self.format_value('00#', 0.0002579), ('0.00026', None))
        self.assertEqual(self.format_value('00#', 1234), ('1200', None))
        self.assertEqual(self.format_value('000#', 0.0002579), ('0.000258', None))
        self.assertEqual(self.format_value('000#', 0.1), ('0.100', None))


if __name__ == '__main__':
    unittest.main()