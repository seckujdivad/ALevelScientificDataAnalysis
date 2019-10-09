import abc
import re
import math


#interface defining all functions
class IMathematicalFunction:
    def __init__(self, *args, autoparse = True):
        self._subfuncs = []
        
        if autoparse:
            for item in args: #check sub functions - if they have already been parsed into objects, leave them. if they are still strings, parse into objects
                if not isinstance(item, IMathematicalFunction):
                    self._subfuncs.append(self.generate_from(item))
                
                else:
                    self._subfuncs.append(item)

    @abc.abstractclassmethod
    def evaluate(self, datatable):
        """
        Evaluate this function using the variables provided in datatable. Recursively evaluates the whole function tree.
        This should be overwritten by the inheriting class.

        Args:
            datatable (dict): all the values to be substituted into variables (defined {variable})
        
        Returns:
            (float): the result of the function
        """
        raise NotImplementedError()

    def generate_from(self, string):
        """
        Breaks down a string into a function that operates on two subfunctions (to be determined by that function). Effectively recursive.

        Args:
            string (str): the string to be broken down
        
        Returns:
            (instance of IMathematicalFunction): the function that this string represents
        """
        #strip redundant brackets
        string = self.strip_brackets(string)

        #look valid places for operators to be
        valid_indexes = []

        bracket_level = 0
        is_variable = False
        for i in range(len(string)):
            if string[i] == '{':
                if is_variable:
                    raise ValueError('{}: can\'t use { when not opening a variable names'.format(i))
                else:
                    is_variable = True
            
            if string[i] == '}':
                if is_variable:
                    is_variable = False
                else:
                    raise ValueError('{}: can\'t use } when not closing a varible name'.format(i))
            
            if string[i] == '(':
                bracket_level += 1
            
            if string[i] == ')':
                if bracket_level > 0:
                    bracket_level -= 1
                
                else:
                    raise ValueError()
            
            if bracket_level == 0 and not is_variable: #operators at this character could be parsable
                valid_indexes.append(i)
        
        #find locations of operators in the string
        matches = []
        for operator in operator_register:
            for match in operator['expression'].finditer(string):
                start, end = match.start(), match.end()

                is_valid = True
                for i in range(start, end, 1):
                    if i not in valid_indexes:
                        is_valid = False
                
                if is_valid:
                    matches.append([match, operator])
        
        if len(matches) == 0:
            raise ValueError('No valid operators found in {}'.format(string))
        
        else:
            operator = matches[0]
            for match in matches:
                if match[1]['priority'] > operator[1]['priority']:
                    operator = match

            raw_items = [string[:operator[0].start()], string[operator[0].end():]]
            raw_items = [self.strip_brackets(item) for item in raw_items]

            if 'default values' in operator[1]:
                for i in range(len(raw_items)):
                    if raw_items[i] == '' and len(operator[1]['default values']) > i:
                        raw_items[i] = operator[1]['default values'][i]

            #check for variable or float
            items = []
            for item in raw_items:
                is_float = True
                for char in item:
                    if char not in '1234567890.':
                        is_float = False

                if is_float:
                        items.append(Float(item))
                
                elif item.startswith('{') and item.endswith('}'):
                    items.append(Variable(item[1:len(item) - 1]))
                
                else:
                    items.append(item)

            return operator[1]['class'](*items)
    
    def strip_brackets(self, string):
        while string.startswith('(') and string.endswith(')'):
            string = string[1:len(string) - 1]
        
        return string


#top level parent function - other classes should interact with this
class Function(IMathematicalFunction):
    def __init__(self, string):
        super().__init__()

        self._subfuncs.append(self.generate_from(string))

    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable)


#sub functions
class Float(IMathematicalFunction):
    def __init__(self, item0):
        super().__init__(autoparse = False)

        self._value = float(item0)
    
    def evaluate(self, datatable):
        return self._value


class Variable(IMathematicalFunction):
    def __init__(self, item0):
        super().__init__(autoparse = False)

        self._name = item0
    
    def evaluate(self, datatable):
        return datatable[self._name]


class Add(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return sum([subfunc.evaluate(datatable) for subfunc in self._subfuncs])


class Subtract(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) - self._subfuncs[1].evaluate(datatable)


class Multiply(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * self._subfuncs[1].evaluate(datatable)


class Division(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) / self._subfuncs[1].evaluate(datatable)


class Power(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return pow(self._subfuncs[0].evaluate(datatable), self._subfuncs[1].evaluate(datatable))


class Sin(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.sin(self._subfuncs[1].evaluate(datatable))


class Cos(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.cos(self._subfuncs[1].evaluate(datatable))


class Tan(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.tan(self._subfuncs[1].evaluate(datatable))


class ArcSin(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.asin(self._subfuncs[1].evaluate(datatable))


class ArcCos(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.acos(self._subfuncs[1].evaluate(datatable))


class ArcTan(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.atan(self._subfuncs[1].evaluate(datatable))


class Deg(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.degrees(self._subfuncs[1].evaluate(datatable))


class Rad(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.radians(self._subfuncs[1].evaluate(datatable))


class Absolute(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * abs(self._subfuncs[1].evaluate(datatable))


class NatLog(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.log(self._subfuncs[1].evaluate(datatable))

class BaseTenLog(IMathematicalFunction):
    def __init__(self, item0, item1):
        super().__init__(item0, item1)
    
    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable) * math.log10(self._subfuncs[1].evaluate(datatable))


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
        "expression": re.compile('[\/]'),
        "priority": 2
    },
    {
        "name": "raise to power",
        "class": Power,
        "expression": re.compile('[\^]'),
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