import abc
import re


#interface defining all functions
class IMathematicalFunction:
    def __init__(self, *args, autoexpand = True):
        self._subfuncs = []

        for item in args:
            if not isinstance(item, IMathematicalFunction):
                self.generate_from(item)
            
            else:
                self._subfuncs.append(item)

    @abc.abstractclassmethod
    def evaluate(self, datatable):
        raise NotImplementedError()

    def generate_from(self, string):
        #strip redundant brackets
        while string.startswith('(') and string.endswith(')'):
            string = string[1:len(string) - 1]

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
            
            if bracket_level == 0 and not is_variable: #this means we can search for functions
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

            self._subfuncs.append(operator[1]['class'](*items))


#top level parent function - other classes should interact with this
class Function(IMathematicalFunction):
    def __init__(self, string):
        super().__init__()

        self.generate_from(string)

    def evaluate(self, datatable):
        return self._subfuncs[0].evaluate(datatable)


#sub functions
class Float(IMathematicalFunction):
    def __init__(self, item0):
        super().__init__(autoexpand = False)

        self._value = float(item0)
    
    def evaluate(self, datatable):
        return self._value


class Variable(IMathematicalFunction):
    def __init__(self, item0):
        super().__init__(autoexpand = False)

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
    }
]