import typing
import math

import sciplot.functions as functions
import sciplot.database as database
import sciplot.datafile as datafile

class Datatable:
    def __init__(self, datafile: datafile.DataFile):
        self._datafile = datafile

        self._variable_ids: typing.List[int] = []
        self._variable_types: typing.List[int] = []
        self._functions: typing.Dict[str, functions.Function] = {}
        self._value_table: typing.Dict[int, typing.List[functions.Value]] = {}
    
    def set_variables(self, variable_ids: typing.List[int]):
        self._variable_ids = variable_ids.copy()

    def load(self, constants_table: typing.Dict[str, functions.Value]):
        constants_table = constants_table.copy()

        var_type_lookup = ["dataset", "formula"]

        #get all functions from the database
        function_table: typing.Dict[str, functions.Function] = {}
        function_var_table: typing.Dict[int, functions.Function] = {}
        for variable_id, expression, name in self._datafile.query(database.Query("SELECT VariableID, Expression, Symbol FROM Formula INNER JOIN Variable ON ID = FormulaID AND Type = 1", [], 1))[0]:
            func = functions.Function(expression)
            func.pre_evaluate(constants_table) #optimise functions
            function_table[name] = func
            function_var_table[variable_id] = func
        
        #get all datasets from the database
        dataset_names_ids: typing.Dict[str, int] = {}
        for dataset_symbol, variable_id in self._datafile.query(database.Query("SELECT Symbol, VariableID FROM Variable WHERE Type = 0", [], 1))[0]:
            dataset_names_ids[dataset_symbol] = variable_id
        
        dependencies = []

        #get data on all columns
        variable_data = []
        for variable_id in self._variable_ids:
            variable_symbol, variable_subid, variable_type = self._datafile.query(database.Query("SELECT Symbol, ID, Type FROM Variable WHERE VariableID = (?);", [variable_id], 2))[0]
            variable_data.append((variable_id, variable_symbol, variable_subid, variable_type))

            if variable_symbol not in function_table: #is a dataset
                dependencies.append((variable_symbol, variable_symbol))
        
        print(dependencies)

        #get formula dependencies
        for variable_id, variable_symbol, variable_subid, variable_type in variable_data:
            if var_type_lookup[variable_type] == "formula":
                for dependency_info in functions.evaluate_dependencies(variable_symbol, function_table):
                    if dependency_info not in dependencies:
                        dependencies.append(dependency_info)
        
        print(dependencies)
        
        #process dependencies
        dependency_table: typing.Dict[str, typing.Dict[str, object]] = {}
        for symbol, dependency in dependencies:
            current_dependency = {"symbol": symbol}

            split_dep_name = dependency.split('.')

            #interpret name
            if symbol == dependency: #constant, formula or dataset
                if symbol in function_table: #formula
                    current_dependency["type"] = "formula"
                
                elif dependency in constants_table: #constant
                    current_dependency["type"] = "constant"

                else: #dataset
                    current_dependency["type"] = "dataset"
                    current_dependency["access mode"] = "same row"
                    current_dependency["processing"] = None
                    current_dependency["subtype"] = None
            
            else: #requires processing
                if len(split_dep_name) > 2: #graph attribute
                    if split_dep_name[0] in ["BEST", "WORST", "WORSTMIN", "WORSTMAX"]:
                        current_dependency["fit line"] = split_dep_name[0].lower()

                    if split_dep_name[1] in ["GRAD", "GRADIENT", "SLOPE"]:
                        current_dependency["subtype"] = "gradient"
                    elif split_dep_name[1] in ["INTERCEPT", "Y-INTERCEPT"]:
                        current_dependency["subtype"] = "intercept"
                    
                    current_dependency["axis names"] = functions.get_variable_names(dependency)

                else:
                    current_dependency["type"] = "value"

                    if split_dep_name[-1] == "MEAN":
                        current_dependency["access mode"] = "single"
                        current_dependency["processing"] = "mean"
                    
                    elif split_dep_name[-1] == "MAX":
                        current_dependency["access mode"] = "single"
                        current_dependency["processing"] = "max"
                    
                    elif split_dep_name[-1] == "MIN":
                        current_dependency["access mode"] = "single"
                        current_dependency["processing"] = "min"
                
                    if current_dependency["symbol"] in function_table:
                        current_dependency["subtype"] = "processed formula"
                    else:
                        current_dependency["subtype"] = None

            dependency_table[dependency] = current_dependency
        
        print("dependencies:")
        print(*["{}: {}".format(key, dependency_table[key]) for key in dependency_table], sep = '\n')
        
        print("dataset contents:")
        #get dataset dependency values
        dataset_table: typing.Dict[str, typing.List[functions.Value]] = {}
        for dependency_name in dependency_table:
            dependency_data = dependency_table[dependency_name]
            if dependency_data["type"] == "dataset" and dependency_data["subtype"] is None:
                values_raw = self._datafile.query(database.Query("SELECT `Value`, DataSet.Uncertainty, DataSet.UncIsPerc, DataSet.UnitCompositeID FROM DataPoint INNER JOIN DataSet ON DataPoint.DataSetID = DataSet.DataSetID INNER JOIN `Variable` ON DataSet.DataSetID = Variable.ID WHERE Symbol = (?) AND Type = 0;", [dependency_data["symbol"]], 1))[0]
                
                values = []
                for value, unc, uncisperc, unit_id in values_raw:
                    value_obj = functions.Value(value, unc, bool(uncisperc))
                    value_obj.units = self._datafile.get_unit_by_id(unit_id)[1]

                    values.append(value_obj)
                
                print(dependency_data["symbol"], values)
        
                dataset_table[dependency_name] = values
        
        #process averages, maxes, mins
        values_to_evaluate = []
        for dependency_name in dependency_table:
            dependency_data = dependency_table[dependency_name]
            if dependency_data["type"] == "value":
                values_to_evaluate.append(dependency_data)

        values_table = {}
        while len(values_to_evaluate) != 0:
            for dependency_name in dependency_table:
                dependency_data = dependency_table[dependency_name]
                if dependency_data in values_to_evaluate:
                    if dependency_data["type"] == "value":
                        values = []
                        if dependency_data["subtype"] is None: #set of values
                            values = dataset_table[dependency_name]

                        else: #function
                            ready_for_evaluation = True
                            func_dependencies = functions.evaluate_dependencies(dependency_data["symbol"], function_table)

                            #Notes on use of break in this loop:
                            #Using a break in this situation is justified as it improves readability and maintains performance in what is an o(n^2) dependency check
                            #The way of achieving the same functionality (breaking out of an iteration) would be achieved with a while loop and a counter. This would
                            #actually decrease readability and require me to add extra boilerplate code for getting the list of dictionary keys, managing the counter
                            #etc. In fact, breaks aren't dissimilar to other syntax like return and raise. Because of this, I have decided to use it in this situation
                            #instead of other, less readable constructs that are a part of structured programming.

                            function_inputs = {}
                            function_input_table = {}
                            dataset_length = -1 #datasets must all be the same length to be properly evaluated
                            for func_dependency_symbol, func_dependency in func_dependencies:
                                if func_dependency in values_to_evaluate:
                                    break #a dependency is yet to be completed, stop compiling dependencies

                                else:
                                    if func_dependency in constants_table:
                                        function_inputs[func_dependency] = constants_table[func_dependency]
                                        function_input_table[func_dependency] = constants_table[func_dependency]

                                    elif func_dependency in values_table:
                                        function_inputs[func_dependency] = values_table[func_dependency]
                                        function_input_table[func_dependency] = values_table[func_dependency]

                                    elif func_dependency in dataset_table:
                                        function_inputs[func_dependency] = dataset_table[func_dependency]

                                        if dataset_length == -1:
                                            dataset_length = len(dataset_table[func_dependency])
                                        elif len(dataset_table[func_dependency]) != dataset_length:
                                            raise ValueError("Dataset '{}' length ({}) differs from length of other datasets ({}), in function '{}' evaluation".format(func_dependency, len(dataset_table[func_dependency]), dataset_length, dependency_name))

                            else: #break not triggered, function can be evaluated using the function inputs
                                for i in range(max(dataset_length, 1)):
                                    for key in function_inputs:
                                        if type(function_inputs[key]) == list:
                                            function_input_table[key] = function_inputs[key][i]
                                    
                                    values.append(functions.evaluate_tree(dependency_data["symbol"], function_table, function_input_table))
                        
                        if len(values) != 0:
                            if dependency_data["processing"] == "max":
                                new_value = functions.Value(max([value.value for value in values]), values[0].absolute_uncertainty, False, values[0].units)
                                values_table[dependency_name] = new_value
                            elif dependency_data["processing"] == "min":
                                new_value = functions.Value(min([value.value for value in values]), values[0].absolute_uncertainty, False, values[0].units)
                                values_table[dependency_name] = new_value
                            elif dependency_data["processing"] == "mean":
                                new_value = functions.Value(sum([value.value for value in values]) / len(values), values[0].percentage_uncertainty / math.sqrt(len(values)), True, values[0].units)
                                values_table[dependency_name] = new_value
                            else:
                                raise ValueError("Invalid dataset processing step '{}' on dependency '{}'".format(dependency_data["processing"], dependency_data))

                            values_to_evaluate.remove(dependency_data)
                    
                    elif dependency_data["type"] == "graphical":
                        raise NotImplementedError("Graphical attributes haven't been implemented in this part of the software yet")
        
        print(values_table)
        print(values_table['area.MEAN'].value)

        
        #evaluate all columns
        for variable_id, variable_symbol, variable_subid, variable_type in variable_data:
            if var_type_lookup[variable_type] == "formula":
                dataset_length = -1
                function_inputs = {}
                function_input_table = {}

                func_dependencies = functions.evaluate_dependencies(variable_symbol, function_table, step_into_processed_sets = False)
                print(func_dependencies)
                for func_dependency_symbol, func_dependency in func_dependencies:
                    print(func_dependency)
                    if func_dependency in constants_table:
                        function_inputs[func_dependency] = constants_table[func_dependency]
                        function_input_table[func_dependency] = constants_table[func_dependency]

                    elif func_dependency in values_table:
                        function_inputs[func_dependency] = values_table[func_dependency]
                        function_input_table[func_dependency] = values_table[func_dependency]

                    elif func_dependency in dataset_table:
                        function_inputs[func_dependency] = dataset_table[func_dependency]

                        if dataset_length == -1:
                            dataset_length = len(dataset_table[func_dependency])
                        elif len(dataset_table[func_dependency]) != dataset_length:
                            raise ValueError("Dataset '{}' length ({}) differs from length of other datasets ({}), in function '{}' evaluation".format(func_dependency, len(dataset_table[func_dependency]), dataset_length, dependency_name))
                
                self._value_table[variable_id] = []

                for i in range(max(dataset_length, 1)):
                    for key in function_inputs:
                        if type(function_inputs[key]) == list:
                            function_input_table[key] = function_inputs[key][i]
                    
                    print(function_input_table)
                    
                    self._value_table[variable_id].append(functions.evaluate_tree(variable_symbol, function_table, function_input_table))
            
            else:
                self._value_table[variable_id] = dataset_table[variable_symbol]
        
        #check column lengths to make sure they all match
        length = -1
        for key in self._value_table:
            if length == -1:
                length = len(self._value_table[key])
            
            elif len(self._value_table[key]) != length:
                raise ValueError("Column length mismatch: {} is of length {}, but length {} is required".format(key, len(self._value_table[key]), length))
        
        print('Final values:')
        print(*[(key, [value.value for value in self._value_table[key]]) for key in self._value_table], sep = '\n')

    def as_rows(self):
        if len(self._value_table) > 0: #transpose row-column layout
            result = []
            row = []

            #check lengths before transposing
            length = -1
            for key in self._value_table:
                if length == -1:
                    length = len(self._value_table[key])
                elif length != len(self._value_table[key]):
                    raise ValueError('Can\'t transpose: column {} has length {}, required length {}'.format(key, len(self._value_table[key]), length))

            for row_index in range(length):
                row.clear()
                for variable_id in self._variable_ids:
                    row.append(self._value_table[variable_id][row_index])
                result.append(row.copy())

            return result

        else:
            return []

    def as_columns(self):
        result = []

        for variable_id in self._variable_ids:
            result.append(self._value_table[variable_id])

        return result