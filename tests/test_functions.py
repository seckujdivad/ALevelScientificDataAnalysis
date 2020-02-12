import unittest
import math
import sys
import os

up1 = os.path.abspath('../')
sys.path.insert(0, up1)

import sciplot.functions as functions #pylint: disable=import-error

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
    
    def test_float(self):
        self.asserter('0.5', 0.5)
    
    def test_functions(self):
        self.asserter('sin0', 0)
        self.asserter('cos0', 1)
        self.asserter('2cos0', 2)
        self.asserter('abs(-1)', 1)
        self.asserter('log(100)', 2)
        self.asserter('ln({})'.format(math.e), 1)
    
    def test_variables(self):
        self.asserter('2*{x}', 6, args = self.convert_datatable({'x': 3}))
        self.asserter('{x}', 3, args = self.convert_datatable({'x': 3}))
    
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
    
    def test_check_circular(self):
        func_table = {'c': functions.Function('{k}'),
                      'k': functions.Function('{r}*2')}
        self.assertEqual(functions.check_circular_dependencies('c', func_table), False)

        func_table['r'] = functions.Function('{c}')
        self.assertEqual(functions.check_circular_dependencies('c', func_table), True)

    def test_evaluate_tree(self):
        func_table = {'c': functions.Function('{k}'),
                      'k': functions.Function('{mass}*2')}
        self.assertEqual(functions.evaluate_tree('c', func_table, self.generic_datatable).value, 50)
    
    def test_evaluate_dependency_trees(self):
        func_table = {'c': functions.Function('{k}*{j}'),
                      'k': functions.Function('{mass.MEAN}*2'),
                      'j': functions.Function('{g}*2')}
        self.assertEqual(functions.evaluate_dependencies('c', func_table), [('mass', 'mass.MEAN'), ('g', 'g')])

    generic_datatable = {'g': functions.Value(9.81, 0.01, False, [(1, 1), (2, 1), (3, -2)]),
                         'volume': functions.Value(532, 0.1, True, [(2, 3)]),
                         'mass': functions.Value(25, 1, False, [(1, 1)])}


class TestVariable(unittest.TestCase):
    def format_value(self, formatstring, value):
        return functions.Value(value).format(formatstring)
    
    def format_scientific(self, value, uncertainty):
        return functions.Value(value, uncertainty, uncertainty_is_percentage = False).format_scientific()

    def test_perctoabs(self):
        self.assertEqual(functions.Value(100, 0.1, True).absolute_uncertainty, 10)
    
    def test_abstoperc(self):
        self.assertEqual(functions.Value(100, 15, False).percentage_uncertainty, 0.15)
    
    def test_format_sigfig(self):
        self.assertEqual(self.format_value('00#', 0.0002579), ('0.00026', None))
        self.assertEqual(self.format_value('00#', 1234), ('1200', None))
        self.assertEqual(self.format_value('000#', 0.0002579), ('0.000258', None))
        self.assertEqual(self.format_value('000#', 0.1), ('0.100', None))
        self.assertEqual(self.format_value('000#', 0.05), ('0.0500', None))
        self.assertEqual(self.format_value('000#', 1), ('1.00', None))
        self.assertEqual(self.format_value('000#', 20), ('20.0', None))
        self.assertEqual(self.format_value('0#', 25), ('30', None))
    
    def test_format_decimal_places(self):
        self.assertEqual(self.format_value('*.*', 10.52), ('10.52', None))
        self.assertEqual(self.format_value('*', 10.52), ('10.52', None))
        self.assertEqual(self.format_value('*.0', 10.52), ('10.5', None))
        self.assertEqual(self.format_value('*.00', 10.52), ('10.52', None))
        self.assertEqual(self.format_value('*.000', 10.52), ('10.520', None))
        self.assertEqual(self.format_value('00.0', 17.52), ('17.5', None))
        self.assertEqual(self.format_value('0.0', 17.52), ('7.5', None))
        self.assertEqual(self.format_value('00.000', 17.52), ('17.520', None))
        self.assertEqual(self.format_value('000.0', 17.52), ('017.5', None))
        self.assertEqual(self.format_value('*0.0*', 17.52), ('17.52', None))
        self.assertEqual(self.format_value('0.*', 17.52), ('7.52', None))
    
    def test_value_close(self):
        self.assertEqual(self.format_value('00.000', 0.0009999999999998899), ('00.001', None))
        self.assertEqual(self.format_value('00.000', 0.053999999999999826), ('00.054', None))
        self.assertEqual(self.format_value('00.000', 0.07799999999999985), ('00.078', None))

        self.assertEqual(self.format_value('000.0', 0.980665), ('001.0', None))
        self.assertEqual(self.format_value('000.0', 1.96133), ('002.0', None))
    
    def test_exponential(self):
        self.assertEqual(self.format_value('0.0e', 253), ('2.5', '2'))
        self.assertEqual(self.format_value('0.00e', 253), ('2.53', '2'))
        self.assertEqual(self.format_value('00.0e', 253), ('25.3', '1'))
        self.assertEqual(self.format_value('0.0e', 0.19), ('1.9', '-1'))

        self.assertEqual(self.format_value('0e', 1.217), ('1', '0'))
        self.assertEqual(self.format_value('0.0e', 1.217), ('1.2', '0'))
        self.assertEqual(self.format_value('0.00e', 1.217), ('1.22', '0'))
        self.assertEqual(self.format_value('0.000e', 1.217), ('1.217', '0'))
    
    def test_scientific(self):
        self.assertEqual(self.format_scientific(324, 10), ('3.2', '2', '0.1'))
        self.assertEqual(self.format_scientific(325, 10), ('3.3', '2', '0.1'))
        self.assertEqual(self.format_scientific(52, 10), ('5', '1', '1'))
        self.assertEqual(self.format_scientific(0.00324, 0.0005), ('3', '-3', '0.5'))
        self.assertEqual(self.format_scientific(0.00324, 0.00005), ('3.2', '-3', '0.05'))
        self.assertEqual(self.format_scientific(1.217, 1), ('1', '0', '1'))
        self.assertEqual(self.format_scientific(1.217, 0.1), ('1.2', '0', '0.1'))
        self.assertEqual(self.format_scientific(1.217, 0.01), ('1.22', '0', '0.01'))
        self.assertEqual(self.format_scientific(1.217, 0.001), ('1.217', '0', '0.001'))


if __name__ == '__main__':
    unittest.main()