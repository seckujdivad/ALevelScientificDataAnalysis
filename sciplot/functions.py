from dataclasses import dataclass
import abc
import re
import math
import typing


class Value:
    """
    Class that holds values with their uncertainties and units. Also provides utilities for converting between percentage and absolute uncertainties as well as some formatting methods.

    NB: Python uses Banker's rounding. This class rounds upwards to resolve equidistant cases as this is the expected behaviour by A-Level physics students. This functionality can be overridden by setting round_use_internal to True.
    """
    def __init__(self, value: typing.Union[float, int, str, bytes, bytearray], uncertainty: float = 0, uncertainty_is_percentage: bool = True, units: typing.List[typing.Tuple[int, float]] = [], round_use_internal: bool = False):
        self.value: float = float(value) #enforce type
        self._uncertainty: float = uncertainty
        self._uncertainty_is_percentage: bool = uncertainty_is_percentage
        self.units = units
        self._round_use_internal: bool = round_use_internal

    def format(self, formatstring, value = None):
        """
        Format this value (or another) using the formatstring
        

        Format strings:
            ends with #: number of zeroes is number of significant figures (00#: 12345 -> 12000)
            else:
                00.00: 1.256 -> 01.26, 1 -> 01.00, -1.2 -> -01.20, 512.53 -> 12.53
                *00.0: 1.256 -> 01.3, 1 -> 01.0, -1.2 -> -01.2, 512.53 -> 512.5
                *.*:   won't change the string
                *:     won't change the string
            

            Appending e will give it as an exponent (5x10^3) where the multiplier (5) has the format string applied to it

        Args:
            formatstring (str): string to format with
            value (float) = None: value to use instead of self.value (if not None)
        
        Returns:
            (multiplier: str, exponent: str or None): value post-formatting. Exponent will be None if exponent form wasn't specified by the format string
        """
        if value is None:
            value = self.value

        if formatstring.endswith('e'): #exponent mode (standard form)
            formatstring = formatstring[:-1]

            exponent = math.floor(math.log10(value))

            pivot = formatstring.find('.')
            if pivot != -1:
                exponent -= pivot
                exponent += 1
                if formatstring.startswith('*'):
                    exponent -= 1

            multiplier = value / pow(10, exponent)

            return (self.format(formatstring, multiplier)[0], str(exponent))

        else: #decimalised mode
            return_string = None
            if formatstring == '*' or formatstring == '*.*':
                return_string = str(value)
            
            elif formatstring.endswith('#'):
                significant_figures = len(formatstring) - 1

                exponent = significant_figures - 1 - math.floor(math.log10(value))

                result_value = value * pow(10, exponent)
                result_value = self.upwards_round(result_value)
                result_value /= pow(10, exponent)

                if result_value.is_integer():
                    result_value = int(result_value)
                
                return_string = str(result_value)

                required_length = len(formatstring) - 1
                return_string_sigfig = 0
                for char in return_string:
                    if (char != '.') and ((char != '0') or (return_string_sigfig > 0)):
                        return_string_sigfig += 1
                
                if return_string_sigfig < required_length:
                    chars_to_add = required_length - return_string_sigfig

                    if '.' not in return_string:
                        return_string += '.'

                    return_string += '0' * chars_to_add
            
            else:
                return_string = str(value)

                #split format string around decimal place
                if formatstring.find('.') == -1:
                    pre_decimal = formatstring
                    post_decimal = ''
                else:
                    pre_decimal = formatstring[:formatstring.find('.')]
                    post_decimal = formatstring[formatstring.find('.') + 1:]

                #interpret format string
                pre_capped = not pre_decimal.startswith('*')
                pre_size = len(pre_decimal)
                if not pre_capped:
                    pre_size -= 1

                post_capped = not post_decimal.endswith('*')
                post_size = len(post_decimal)
                if not post_capped:
                    post_size -= 1
                
                #split value to format around decimal place
                return_pivot = return_string.find('.')
                if return_pivot == -1:
                    pre_return = return_string
                    post_return = ''
                else:
                    pre_return = return_string[:return_pivot]
                    post_return = return_string[return_pivot + 1:]
                
                if pre_size > len(pre_return):
                    pre_return = ('0' * (pre_size - len(pre_return))) + pre_return
                elif (pre_size < len(pre_return)) and pre_capped:
                    pre_return = pre_return[0 - len(pre_return) + pre_size:]
                
                if post_decimal == '':
                    post_return = ''
                elif post_size > len(post_return):
                    post_return += '0' * (post_size - len(post_return))
                elif (post_size < len(post_return)) and post_capped:
                    post_return = str(int(self.upwards_round(int(post_return) / pow(10, len(post_return) - post_size))))
                
                if post_return == '':
                    return_string = pre_return
                elif pre_return == '':
                    return_string = '0.{}'.format(post_return)
                else:
                    return_string = '{}.{}'.format(pre_return, post_return)

            return (return_string, None)
    
    def format_scientific(self):
        """
        Returns self.value in scientific form (standard form, uncertainty to 1 sig fig, multiplier to same number of decimal places as uncertainty)

        Returns:
            (str, str, str): multiplier, exponent, absolute uncertainty
        """
        multiplier, exponent = self.format('0.0e')
        exponent = int(exponent)
        uncertainty = self.format('0#', self.absolute_uncertainty / pow(10, exponent))[0]
        
        multiplier, exponent = self.format('0.{}e'.format('0' * int(0 - math.log10(self.percentage_uncertainty))))

        return multiplier, exponent, uncertainty
    
    def upwards_round(self, num: float):
        if self._round_use_internal:
            return round(num)
        else:
            return int(num + 0.5)

    #properties
    def _get_unc_abs(self):
        if self._uncertainty_is_percentage:
            return self._uncertainty * self.value
        else:
            return self._uncertainty
    
    def _set_unc_abs(self, value):
        self._uncertainty = value
        self._uncertainty_is_percentage = False
    
    def _get_unc_perc(self):
        if self._uncertainty_is_percentage:
            return self._uncertainty
        else:
            return self._uncertainty / self.value
    
    def _set_unc_perc(self, value):
        self._uncertainty = value
        self._uncertainty_is_percentage = True
    
    absolute_uncertainty = property(_get_unc_abs, _set_unc_abs)
    percentage_uncertainty = property(_get_unc_perc, _set_unc_perc)

t_datatable = typing.Dict[str, Value] #composite type hint


#interface defining all functions
class IMathematicalFunction:
    def __init__(self, *args: typing.List[typing.Union[object, str]], autoparse: bool = True):
        self._subfuncs = []
        
        if autoparse:
            for item in args: #check sub functions - if they have already been parsed into objects, leave them. if they are still strings, parse into objects
                if isinstance(item, IMathematicalFunction):
                    self._subfuncs.append(item)
                else:
                    self._subfuncs.append(self.generate_from(item))

    def evaluate(self, datatable: t_datatable):
        """
        Evaluate this function using the variables provided in datatable. Recursively evaluates the whole function tree.

        Args:
            datatable (dict of str: Value): all the values to be substituted into variables (defined {variable})
        
        Returns:
            (Value): the result of the function
        """
        evaluated_subfuncs = [subfunc.evaluate(datatable) for subfunc in self._subfuncs]

        value = self._evaluate_value(datatable, evaluated_subfuncs)
        uncertainty, uncertainty_is_percentage = self._evaluate_uncertainty(datatable, evaluated_subfuncs)

        units = self._evaluate_units(datatable, evaluated_subfuncs)
        to_remove = []
        for i in range(len(units)):
            if units[i][1] == 0:
                to_remove.append(i)
        to_remove.reverse()
        for i in to_remove:
            units.pop(i)
        
        return Value(value, uncertainty, uncertainty_is_percentage, units)

    @abc.abstractclassmethod
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        """
        Calculate the resultant value of this function using the variables provided in datatable

        Args:
            datatable (dict of str: Value): all the values to be substituted into variables (defined {variable})
        
        Returns:
            (float): the result of the function
        """
        raise NotImplementedError()

    @abc.abstractclassmethod
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        """
        Calculates the uncertainty of the Value object to be returned by evaluate
        The uncertainty is calculated using approximations of functions that are taught to Physics students at A-Level, not by calculating the range of outputs

        Args:
            datatable (dict of str: Value): values to be substituted into variables
        
        Returns:
            (float, bool): the uncertainty and whether it is percentage
        """
        raise NotImplementedError()

    @abc.abstractclassmethod
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        """
        Calculates the resulting units of the Value object to be returned by evaluate

        Args:
            datatable (dict of str: Value): values to be substituted into variables
        
        Returns:
            (list of (int, float)): the resultant units
        """
        raise NotImplementedError()

    def generate_from(self, string: str):
        """
        Breaks down a string into a function that operates on two subfunctions (to be determined by that function). Effectively recursive.

        Args:
            string (str): the string to be broken down
        
        Returns:
            (instance of IMathematicalFunction): the function that this string represents
        """
        #strip redundant brackets
        string = _strip_brackets(string)
        string = _remove_all_spaces(string)

        #look for valid places for operators to be
        search_regions = []
        current_segment = ''
        start_index = 0

        bracket_level = 0
        is_variable = False
        for i in range(len(string)):
            if string[i] == '{': #brackets inside a variable don't affect operators, so don't count them
                if is_variable:
                    raise ValueError('{}: can\'t use { when not opening a variable names'.format(i))
                else:
                    is_variable = True
            
            if string[i] == '(':
                bracket_level += 1
            
            if bracket_level == 0 and not is_variable: #operators at this character could be parsable
                if current_segment == '':
                    start_index = i
                current_segment += string[i]

            elif current_segment != '': #end of valid segment, add the completed segment to search_regions
                search_regions.append((start_index, current_segment))
                current_segment = ''
            
            if string[i] == '}':
                if is_variable:
                    is_variable = False
                else:
                    raise ValueError('{}: can\'t use } when not closing a variable name'.format(i))
            
            if string[i] == ')':
                if bracket_level > 0:
                    bracket_level -= 1
                
                else:
                    raise ValueError('In expression "{}" at {}: can\'t close an unopened bracket pair'.format(string, i))
            
        
        if current_segment != '': #if there is a leftover search segment add it to search segments
            search_regions.append((start_index, current_segment))
            current_segment = ''
        
        if bracket_level != 0:
            raise ValueError('In expression "{}": {} bracket(s) were not closed'.format(string, bracket_level))
            
        if is_variable:
            raise ValueError('In expression "{}": a variable was not closed with } before the end of the expression'.format(string))
        
        #find locations of operators in the string
        matches = []
        for operator in operator_register:
            for start_index, segment in search_regions:
                for match in operator['expression'].finditer(segment):
                    start, end = start_index + match.start(), start_index + match.end()
                    matches.append([{'start': start, 'end': end}, operator])
        
        if len(matches) == 0:
            is_float = True
            items = []
            for char in string:
                if char not in '1234567890.':
                    is_float = False

            if is_float:
                return Float(string)
            
            elif string.startswith('{') and string.endswith('}') and '}' not in string[1:-1]: #check for variable
                return Variable(string[1:len(string) - 1])

            else:
                raise ValueError('No valid operators found in "{}"'.format(string))
        
        else:
            #find operators that overlap and remove them first
            has_overlap = True
            while has_overlap:
                to_remove = None

                for match in matches:
                    for other_match in matches:
                        if match != other_match:
                            if (match[0]['start'] <= other_match[0]['start']) and (match[0]['end'] >= other_match[0]['end']):
                                to_remove = other_match

                            elif (((match[0]['start'] <= other_match[0]['start']) and (match[0]['end'] <= other_match[0]['end']) and (match[0]['end'] >= other_match[0]['start']))
                                 or ((match[0]['end'] >= other_match[0]['end']) and (match[0]['start'] >= other_match[0]['start']) and (match[0]['start'] <= other_match[0]['end']))):
                                match_len = match[0]['end'] - match[0]['start']
                                other_match_len = other_match[0]['end'] - other_match[0]['start']

                                if match_len > other_match_len:
                                    to_remove = other_match
                                elif match_len == other_match_len:
                                    raise ValueError('Two operators of equal length {} are competing for the same match in expression "{}" - "{}": ({}, {}), "{}": ({}, {}). This conflict can\'t be resolved without changing the expression or modifying the capture expressions at the bottom of the functions module to avoid triggering both conditions.'.format(match_len, string, match[1]['name'], match[0]['start'], match[0]['end'], other_match[1]['name'], other_match[0]['start'], other_match[0]['end']))

                if to_remove is None:
                    has_overlap = False
                else:
                    matches.remove(to_remove)

            #find highest priority operator and process that first
            operator = matches[0]
            for match in matches:
                if match[1]['priority'] > operator[1]['priority']:
                    operator = match

            #remove the operator and split the strings either side
            raw_items = [string[:operator[0]['start']], string[operator[0]['end']:]]
            raw_items = [_strip_brackets(item) for item in raw_items]

            #insert a default value for the operator if the value is missing (e.g. sin2 -> 1sin(2))
            for i in range(len(raw_items)):
                if raw_items[i] == '':
                    has_default = False
                    if 'default values' in operator[1]:
                        if len(operator[1]['default values']) > i:
                            if operator[1]['default values'][i] is not None:
                                raw_items[i] = operator[1]['default values'][i]
                                has_default = True
                    
                    if not has_default:
                        raise ValueError('In expression "{}": operand {} was not supplied for operator "{}" and a default value couldn\'t be found'.format(string, i, operator[1]['name']))

            #check for variable or float
            items = []
            for item in raw_items:
                #check for float
                is_float = True
                for char in item:
                    if char not in '1234567890.':
                        is_float = False

                if is_float:
                    items.append(Float(item))
                
                elif item.startswith('{') and item.endswith('}') and '}' not in item[1:-1]: #check for variable
                    items.append(Variable(item[1:len(item) - 1]))
                
                else:
                    items.append(item) #further evaluation needed

            return operator[1]['class'](*items)
    
    def is_static(self, constants: t_datatable): #to be overridden by leaves
        """
        Returns whether or not this branch of the tree is static (depends on the datatable)

        Args:
            constants (dict str: float): the variables in the datatable that are constant
        
        Returns:
            (bool): whether or not this branch of the tree is static
        """
        return False not in [subfunc.is_static(constants) for subfunc in self._subfuncs]
    
    def pre_evaluate(self, constants: t_datatable):
        """
        Pre-evaluate sections of the tree that are static as determined by is_static

        Args:
            constants (dict str: float): the variables in the datatable that are constant
        
        Returns:
            (self): This section of the tree is dynamic
            (Float): This section of the tree is static and has been evaluated down to this Float object
        """
        if self.is_static(constants):
            return Float(self.evaluate(constants))
        
        else:
            for i in range(len(self._subfuncs)):
                self._subfuncs[i] = self._subfuncs[i].pre_evaluate(constants)

            return self
    
    def num_nodes(self, include_branches = True): #to be overwritten by leaves
        """
        Calculates the complexity of tree based on the number of nodes

        Args:
            include_branches (bool: True): specifies whether or not a branch should add to the count
        
        Returns:
            (int): complexity of this branch
        """
        total = sum([subfunc.num_nodes(include_branches) for subfunc in self._subfuncs])

        if include_branches:
            return total + 1
        else:
            return total
    
    def evaluate_dependencies(self): #to be overwritten by leaves
        """
        Finds the variables that this function is dependent on (the variables that must be included in the datatable)

        Returns:
            (list of str): the names of the variables this function is dependent on
        """
        dependencies = [subfunc.evaluate_dependencies() for subfunc in self._subfuncs]
        result = []
        for dependency_list in dependencies:
            for name in dependency_list:
                if name not in result:
                    result.append(name)
        return result


#root - other classes should interact with this
class Function(IMathematicalFunction):
    def __init__(self, string: str):
        super().__init__()

        self._subfuncs.append(self.generate_from(string))

    def evaluate(self, datatable: t_datatable):
        return self._subfuncs[0].evaluate(datatable)


#sub functions
# leaves
class Float(IMathematicalFunction):
    def __init__(self, item0: str, uncertainty: typing.Union[float, str, Value] = 0):
        super().__init__(autoparse = False)

        self._value: Value = None

        if type(item0) in [str, float]:
            self._value = Value(item0)
        elif isinstance(item0, Value):
            self._value = item0
        else:
            raise TypeError('item0 must be of type float, str or Value, not {} (contents {})'.format(type(item0), item0))

        self._uncertainty = uncertainty
    
    def evaluate(self, datatable: t_datatable):
        return self._value
    
    def is_static(self, constants: t_datatable):
        return True
    
    def num_nodes(self, include_branches = True):
        return 1
    
    def evaluate_dependencies(self):
        return []


class Variable(IMathematicalFunction):
    def __init__(self, item0: str):
        super().__init__(autoparse = False)

        self._name = item0
    
    def evaluate(self, datatable: t_datatable):
        return datatable[self._name]
    
    def is_static(self, constants: t_datatable):
        return self._name in constants
    
    def num_nodes(self, include_branches = True):
        return 1
    
    def evaluate_dependencies(self):
        return [self._name]


# branches
class Add(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value + evaluated_subfuncs[1].value
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].absolute_uncertainty + evaluated_subfuncs[1].absolute_uncertainty, False)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        if evaluated_subfuncs[0].units == evaluated_subfuncs[1].units:
            return evaluated_subfuncs[0].units
        else:
            return []


class Subtract(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value - evaluated_subfuncs[1].value
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].absolute_uncertainty + evaluated_subfuncs[1].absolute_uncertainty, False)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        if evaluated_subfuncs[0].units == evaluated_subfuncs[1].units:
            return evaluated_subfuncs[0].units
        else:
            return []


class Multiply(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * evaluated_subfuncs[1].value
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        result = evaluated_subfuncs[0].units.copy()
        for unit_id, power in evaluated_subfuncs[1].units:
            to_add = None
            to_remove = -1
            for i in range(len(result)):
                if result[i][0] == unit_id:
                    to_add = (unit_id, result[i][1] + power)
                    to_remove = i

            if to_add is None:
                result.append((unit_id, power))
            else:
                result.pop(to_remove)
                result.append(to_add)
        
        return result


class Division(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value / evaluated_subfuncs[1].value
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        result = evaluated_subfuncs[0].units.copy()
        for unit_id, power in evaluated_subfuncs[1].units:
            to_add = None
            to_remove = -1
            for i in range(len(result)):
                if result[i][0] == unit_id:
                    to_add = (unit_id, result[i][1] - power)
                    to_remove = i

            if to_add is None:
                result.append((unit_id, 0 - power))
            else:
                result.pop(to_remove)
                result.append(to_add)
        
        return result


class Power(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return pow(evaluated_subfuncs[0].value, evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        #ignore the uncertainty on the 'raise to' value as it is almost always 0
        return (evaluated_subfuncs[0].percentage_uncertainty * evaluated_subfuncs[1].value, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return [(unit_id, power * evaluated_subfuncs[1].value) for unit_id, power in evaluated_subfuncs[0].units]


class Sin(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.sin(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class Cos(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.cos(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class Tan(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.tan(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class ArcSin(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.asin(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class ArcCos(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.acos(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class ArcTan(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.atan(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class Deg(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.degrees(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class Rad(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.radians(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


class Absolute(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * abs(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        result = evaluated_subfuncs[0].units.copy()
        for unit_id, power in evaluated_subfuncs[1].units:
            to_add = None
            to_remove = -1
            for i in range(len(result)):
                if result[i][0] == unit_id:
                    to_add = (unit_id, result[i][1] + power)
                    to_remove = i

            if to_add is None:
                result.append((unit_id, power))
            else:
                result.pop(to_remove)
                result.append(to_add)
        
        return result


class NatLog(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.log(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units

class BaseTenLog(IMathematicalFunction):
    def __init__(self, item0: str, item1: str):
        super().__init__(item0, item1)
    
    def _evaluate_value(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].value * math.log10(evaluated_subfuncs[1].value)
    
    def _evaluate_uncertainty(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return (evaluated_subfuncs[0].percentage_uncertainty + evaluated_subfuncs[1].percentage_uncertainty, True)
    
    def _evaluate_units(self, datatable: t_datatable, evaluated_subfuncs: typing.List[Value]):
        return evaluated_subfuncs[0].units


#lookup for all operators: variable and float aren't registered as they end each branch so they are detected differently
operator_register = [
    {
        "name": "addition",
        "class": Add,
        "expression": re.compile('[+]'),
        "priority": 4,
        "default values": ["0"]
    },
    {
        "name": "subtraction",
        "class": Subtract,
        "expression": re.compile('[-]'),
        "priority": 5,
        "default values": ["0"]
    },
    {
        "name": "multiplication",
        "class": Multiply,
        "expression": re.compile('[*]'),
        "priority": 3,
    },
    {
        "name": "division",
        "class": Division,
        "expression": re.compile('[\\/]'),
        "priority": 2
    },
    {
        "name": "raise to power",
        "class": Power,
        "expression": re.compile('[\\^]'),
        "priority": 1
    },
    {
        "name": "sine",
        "class": Sin,
        "expression": re.compile('[s][i][n]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "cosine",
        "class": Cos,
        "expression": re.compile('[c][o][s]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "tangent",
        "class": Tan,
        "expression": re.compile('[t][a][n]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "arcsine",
        "class": ArcSin,
        "expression": re.compile('[a][s][i][n]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "arccosine",
        "class": ArcCos,
        "expression": re.compile('[a][c][o][s]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "arctangent",
        "class": ArcTan,
        "expression": re.compile('[a][t][a][n]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "arcsine verbose",
        "class": ArcSin,
        "expression": re.compile('[a][r][c][s][i][n]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "arccosine verbose",
        "class": ArcCos,
        "expression": re.compile('[a][r][c][c][o][s]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "arctangent verbose",
        "class": ArcTan,
        "expression": re.compile('[a][r][c][t][a][n]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "radians to degrees",
        "class": Deg,
        "expression": re.compile('[d][e][g]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "degrees to radians",
        "class": Rad,
        "expression": re.compile('[r][a][d]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "absolute value",
        "class": Absolute,
        "expression": re.compile('[a][b][s]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "natural logarithm",
        "class": NatLog,
        "expression": re.compile('[l][n]'),
        "priority": 0,
        "default values": ["1"]
    },
    {
        "name": "base 10 logarithm",
        "class": BaseTenLog,
        "expression": re.compile('[l][o][g]'),
        "priority": 0,
        "default values": ["1"]
    }
]


#tree operations
def check_circular_dependencies(function_name: str, functions: typing.Dict[str, Function]):
    return _chk_circular([function_name], functions[function_name].evaluate_dependencies(), functions)

def _chk_circular(tree: typing.List[str], function_names: typing.List[str], functions: typing.Dict[str, Function]):
    for key in function_names:
        if key in tree:
            return True

        if key in functions:
            tree.append(key)

            dependencies = functions[key].evaluate_dependencies()

            if _chk_circular(tree, dependencies, functions):
                return True

            tree.pop(len(tree) - 1)
    
    return False


#utility functions
def _strip_brackets(string):
    while string.startswith('(') and string.endswith(')'):
        string = string[1:-1]
    
    return string

def _remove_all_spaces(string):
    return string.replace(' ', '')