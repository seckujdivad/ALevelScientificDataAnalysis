from dataclasses import dataclass
import abc
import re
import math
import typing


class Value:
    def __init__(self, value, uncertainty: float = 0, uncertainty_is_percentage: bool = True, units: typing.List[typing.Tuple[int, float]] = []):
        self.value: float = float(value) #enforce type
        self._uncertainty: float = uncertainty
        self._uncertainty_is_percentage: bool = uncertainty_is_percentage
        self.units = units
    
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

t_datatable = typing.Dict[str, Value] #type hint


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
            
            if string[i] == '}':
                if is_variable:
                    is_variable = False
                else:
                    raise ValueError('{}: can\'t use } when not closing a variable name'.format(i))
            
            if string[i] == '(':
                bracket_level += 1
            
            if string[i] == ')':
                if bracket_level > 0:
                    bracket_level -= 1
                
                else:
                    raise ValueError('In expression "{}" at {}: can\'t close an unopened bracket pair'.format(string, i))
            
            if bracket_level == 0 and not is_variable: #operators at this character could be parsable
                if current_segment == '':
                    start_index = i
                current_segment += string[i]

            elif current_segment != '': #end of valid segment, add the completed segment to search_regions
                search_regions.append((start_index, current_segment))
                current_segment = ''
        
        if current_segment != '': #if there is a leftover search segment add it to search segments
            search_regions.append((start_index, current_segment))
            current_segment = ''
        
        if bracket_level != 0:
            raise ValueError('In expression "{}": {} bracket(s) were not closed'.format(string, bracket_level))
        
        #find locations of operators in the string
        matches = []
        for operator in operator_register:
            for start_index, segment in search_regions:
                for match in operator['expression'].finditer(segment):
                    start, end = start_index + match.start(), start_index + match.end()
                    matches.append([{'start': start, 'end': end}, operator])
        
        if len(matches) == 0:
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
            if 'default values' in operator[1]:
                for i in range(len(raw_items)):
                    if raw_items[i] == '' and len(operator[1]['default values']) > i:
                        raw_items[i] = operator[1]['default values'][i]

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
                
                elif item.startswith('{') and item.endswith('}'): #check for variable
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

#utility functions
def _strip_brackets(string):
    while string.startswith('(') and string.endswith(')'):
        string = string[1:-1]
    
    return string

def _remove_all_spaces(string):
    return string.replace(' ', '')