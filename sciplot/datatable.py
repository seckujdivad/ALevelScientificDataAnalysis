import typing
import math

import sciplot
import sciplot.functions as functions
import sciplot.database as database
import sciplot.datafile as datafile
import sciplot.graphing as graphing


class Datatable:
    """
    An object that evaluates multiple variables by ID and creates a table out of them ready for evaluation

    Args:
        datafile (Datafile): datafile to get variables from
    """
    def __init__(self, datafile: datafile.DataFile):
        self._datafile = datafile

        self._variable_ids: typing.List[int] = []
        self._value_table: typing.Dict[int, typing.List[sciplot.Value]] = {}
    
    def set_variables(self, variable_ids: typing.List[int]):
        """
        Set the variable ids of the columns to be used in calls to load.
        The order they are given is the order they will be given in in as_rows and as_columns

        Args:
            variable_ids (list of int): list of variable primary keys
        """
        self._variable_ids = variable_ids.copy()

    def load(self, constants_table: typing.Dict[str, sciplot.Value]):
        """
        Load the variables given in set_variables into memory where they can be retrieved using as_rows and as_columns

        Args:
            constants_table (dict of str: sciplot.Value): table containing constant values and their symbols for use while evaluating functions
        """
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

        #check for circular dependencies
        #they should be checked for at submission time, but it is conceivable that there is some unknown submission/modification order
        #that could slip one by
        #also, the database could be maliciously crafted
        for function_name in function_table:
            if sciplot.functions.check_circular_dependencies(function_name, function_table):
                raise RuntimeError("Function '{}' has circular dependencies. Cancelling load".format(function_name))
        
        #get all datasets from the database
        dataset_names_ids: typing.Dict[str, int] = {}
        for dataset_symbol, variable_id in self._datafile.query(database.Query("SELECT Symbol, VariableID FROM Variable WHERE Type = 0", [], 1))[0]:
            dataset_names_ids[dataset_symbol] = variable_id
        
        dependencies = [] #get names of all dependencies (things that need to be evaluated before the final variables can be evaluated)

        #get data on all columns
        variable_data = []
        for variable_id in self._variable_ids:
            variable_symbol, variable_subid, variable_type = self._datafile.query(database.Query("SELECT Symbol, ID, Type FROM Variable WHERE VariableID = (?);", [variable_id], 2))[0]
            variable_data.append((variable_id, variable_symbol, variable_subid, variable_type))

            if variable_symbol not in function_table: #is a dataset
                dependencies.append((variable_symbol, variable_symbol))
        
        #get formula dependencies
        for variable_id, variable_symbol, variable_subid, variable_type in variable_data:
            if var_type_lookup[variable_type] == "formula":
                for dependency_info in functions.evaluate_dependencies(variable_symbol, function_table):
                    if dependency_info not in dependencies:
                        dependencies.append(dependency_info)
        
        #process dependencies so that they can be retrieved and evaluated in the correct order
        dependency_table: typing.Dict[str, typing.Dict[str, object]] = {}
        for symbol, dependency in dependencies:
            current_dependency = {"symbol": symbol}

            split_dep_name = dependency.split('.')

            #interpret name
            if dependency in function_table: #formula
                current_dependency["type"] = "formula"
            
            elif dependency in constants_table: #constant
                current_dependency["type"] = "constant"

            elif len(split_dep_name) > 2: #graph attribute
                current_dependency["type"] = "graphical"

                if split_dep_name[0] in ["BEST", "WORST", "WORSTMIN", "WORSTMAX"]:
                    current_dependency["fit line"] = split_dep_name[0].lower()

                if split_dep_name[1] in ["GRAD", "GRADIENT", "SLOPE"]:
                    current_dependency["subtype"] = "gradient"
                elif split_dep_name[1] in ["INTERCEPT", "Y-INTERCEPT"]:
                    current_dependency["subtype"] = "intercept"
                
                current_dependency["axis names"] = functions.get_variable_names(dependency, split_graphs = True)

            elif split_dep_name[-1] in ["MEAN", "MAX", "MIN"]: #processed data set
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
            
                if current_dependency["symbol"] in function_table: #processed data set is actually a formula, not a data set
                    current_dependency["subtype"] = "processed formula"
                else:
                    current_dependency["subtype"] = None
            
            else: #dataset
                current_dependency["type"] = "dataset"
                current_dependency["access mode"] = "same row"
                current_dependency["processing"] = None
                current_dependency["subtype"] = None

            dependency_table[dependency] = current_dependency
        
        #get dataset dependency values
        dataset_table: typing.Dict[str, typing.List[sciplot.Value]] = {}
        for dependency_name in dependency_table:
            dependency_data = dependency_table[dependency_name]
            if dependency_data["type"] == "dataset" and dependency_data["subtype"] is None:
                values_raw = self._datafile.query(database.Query("SELECT `Value`, DataSet.Uncertainty, DataSet.UncIsPerc, DataSet.UnitCompositeID FROM DataPoint INNER JOIN DataSet ON DataPoint.DataSetID = DataSet.DataSetID INNER JOIN `Variable` ON DataSet.DataSetID = Variable.ID WHERE Symbol = (?) AND Type = 0 ORDER BY DataPoint.DataPointID ASC;", [dependency_data["symbol"]], 1))[0]
                
                values = []
                for value, unc, uncisperc, unit_id in values_raw:
                    value_obj = functions.Value(value, unc, bool(uncisperc))
                    value_obj.units = self._datafile.get_unit_by_id(unit_id)[1]

                    values.append(value_obj)
        
                dataset_table[dependency_name] = values
        
        #pick out averages, maxes, mins and graphical data for processing
        values_to_evaluate = []
        for dependency_name in dependency_table:
            dependency_data = dependency_table[dependency_name]
            if dependency_data["type"] in ["value", "graphical"]:
                values_to_evaluate.append(dependency_data)

        #run passes of the dependency table looking for dependencies that can be evaluated until all have been evaluated
        values_table = {}
        last_loop = len(values_to_evaluate)
        while len(values_to_evaluate) != 0:
            for dependency_name in dependency_table:
                dependency_data = dependency_table[dependency_name]

                if dependency_data in values_to_evaluate:
                    if dependency_data["type"] == "value":
                        values = []
                        if dependency_data["subtype"] is None: #set of values
                            values = dataset_table[dependency_name]

                        else: #function
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
                            for func_dependency_symbol, func_dependency in func_dependencies: #gather all dependencies
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

                                        if dataset_length == -1: #no dataset length has yet been encountered - all other data sets must be of this length
                                            dataset_length = len(dataset_table[func_dependency]) #length mismatch, exit
                                        elif len(dataset_table[func_dependency]) != dataset_length:
                                            raise ValueError("Dataset '{}' length ({}) differs from length of other datasets ({}), in function '{}' evaluation".format(func_dependency, len(dataset_table[func_dependency]), dataset_length, dependency_name))

                            else: #break not triggered, function can be evaluated using the function inputs
                                for i in range(max(dataset_length, 1)):
                                    for key in function_inputs:
                                        if type(function_inputs[key]) == list:
                                            function_input_table[key] = function_inputs[key][i]
                                    
                                    values.append(functions.evaluate_tree(dependency_data["symbol"], function_table, function_input_table))
                        
                        if len(values) != 0: #calculate statistical operation
                            if dependency_data["processing"] == "max":
                                new_value = sciplot.Value(max([value.value for value in values]), values[0].absolute_uncertainty, False, values[0].units)
                                values_table[dependency_name] = new_value
                            elif dependency_data["processing"] == "min":
                                new_value = sciplot.Value(min([value.value for value in values]), values[0].absolute_uncertainty, False, values[0].units)
                                values_table[dependency_name] = new_value
                            elif dependency_data["processing"] == "mean":
                                new_value = sciplot.Value(sum([value.value for value in values]) / len(values), values[0].percentage_uncertainty / math.sqrt(len(values)), True, values[0].units)
                                values_table[dependency_name] = new_value
                            else:
                                raise ValueError("Invalid dataset processing step '{}' on dependency '{}'".format(dependency_data["processing"], dependency_data))

                            values_to_evaluate.remove(dependency_data)
                    
                    elif dependency_data["type"] == "graphical": #use graphing submodule
                        data_table = Datatable(self._datafile) #load table to be graphed (recursive process)
                        variable_ids = [self._datafile.query(database.Query("SELECT VariableID FROM Variable WHERE Symbol = (?)", [symbol], 2))[0][0] for symbol in current_dependency["axis names"]]
                        variable_ids.reverse() #change from yx to xy
                        data_table.set_variables(variable_ids)
                        data_table.load(constants_table)

                        #check graphing inputs
                        if len(data_table.as_columns()) != 2:
                            raise ValueError('{} doesn\'t have exactly 2 columns'.format(dependency_name))
                            
                        if len(data_table.as_rows()) == 0:
                            raise ValueError('{} is empty'.format(dependency_name))

                        fit_lines = graphing.FitLines(data_table)

                        value = None
                        
                        #get correct fit line and attribute
                        if dependency_data["fit line"] == "best":
                            fit_lines.calculate_best_fit()
                            if current_dependency["subtype"] == "gradient":
                                value = fit_lines.fit_best_gradient
                            else:
                                value = fit_lines.fit_best_intercept
                            
                        else:
                            fit_lines.calculate_all()

                            if current_dependency["subtype"] == "gradient":
                                if current_dependency["fit line"] == "worst":
                                    value = fit_lines.fit_worst_gradient
                                elif current_dependency["fit line"] == "worstmin":
                                    value = fit_lines.fit_worst_min_gradient
                                elif current_dependency["fit line"] == "worstmax":
                                    value = fit_lines.fit_worst_max_gradient
                                
                            else:
                                if current_dependency["fit line"] == "worst":
                                    value = fit_lines.fit_worst_intercept
                                elif current_dependency["fit line"] == "worstmin":
                                    value = fit_lines.fit_worst_min_intercept
                                elif current_dependency["fit line"] == "worstmax":
                                    value = fit_lines.fit_worst_max_intercept
                        
                        #store value in Value object
                        values_table[dependency_name] = sciplot.Value(value)

                        #get correct units
                        if current_dependency["subtype"] == "gradient": #divide the two units - subtract x powers from y powers
                            units_x = data_table.as_rows()[0][0].units
                            units_y = data_table.as_rows()[0][1].units
                            unit_dict_x = {key: 0 - value for key, value in units_x}
                            unit_dict_y = {key: value for key, value in units_y}

                            result = {}
                            for unit_dict in [unit_dict_x, unit_dict_y]:
                                for key in unit_dict:
                                    if key in result:
                                        result[key] += unit_dict[key]
                                    else:
                                        result[key] = unit_dict[key]

                            values_table[dependency_name].units = [(key, result[key]) for key in result]

                        else: #y intercept has units of y axis
                            values_table[dependency_name].units = data_table.as_rows()[0][1].units
                        
                        #don't leave these two large objects for the garbage collector, get rid of them as soon as possible to reduce risk of memory errors
                        del fit_lines
                        del data_table

                        values_to_evaluate.remove(dependency_data)

            if last_loop == len(values_to_evaluate): #no more dependencies will be evaluateable - this state should never be achieved, but just in case this inexpensive catch is here
                raise RuntimeError("No more dependencies can be evaluated - stuck on {} left in an infinite loop".format(last_loop))

            last_loop = len(values_to_evaluate)

        #evaluate all columns
        for variable_id, variable_symbol, variable_subid, variable_type in variable_data:
            if var_type_lookup[variable_type] == "formula":
                dataset_length = -1
                function_inputs = {} #inputs for the function, stored as values or lists of values
                function_input_table = {} #inputs for the function containing a specific row (samples from function_inputs)

                func_dependencies = functions.evaluate_dependencies(variable_symbol, function_table, step_into_processed_sets = False)
                for func_dependency_symbol, func_dependency in func_dependencies: #produce a table of the correct inputs
                    if func_dependency in constants_table:
                        function_inputs[func_dependency] = constants_table[func_dependency]
                        function_input_table[func_dependency] = constants_table[func_dependency]

                    elif func_dependency in values_table:
                        function_inputs[func_dependency] = values_table[func_dependency]
                        function_input_table[func_dependency] = values_table[func_dependency]

                    elif func_dependency in dataset_table:
                        function_inputs[func_dependency] = dataset_table[func_dependency]

                        if dataset_length == -1: #has no length (e.g. a formula, give it the length of its dependency)
                            dataset_length = len(dataset_table[func_dependency])
                        elif len(dataset_table[func_dependency]) != dataset_length:
                            raise ValueError("Dataset '{}' length ({}) differs from length of other datasets ({}), in function '{}' evaluation".format(func_dependency, len(dataset_table[func_dependency]), dataset_length, dependency_name))
                
                self._value_table[variable_id] = []

                for i in range(max(dataset_length, 1)): #if dataset length is -1 (no inputs have a length) default to one row
                    for key in function_inputs:
                        if type(function_inputs[key]) == list:
                            function_input_table[key] = function_inputs[key][i]
                    
                    self._value_table[variable_id].append(functions.evaluate_tree(variable_symbol, function_table, function_input_table))
            
            else: #datasets have all already been fetched
                self._value_table[variable_id] = dataset_table[variable_symbol]
        
        #check column lengths to make sure they all match
        length = -1
        for key in self._value_table:
            if length == -1:
                length = len(self._value_table[key])
            
            elif len(self._value_table[key]) != length:
                raise ValueError("Column length mismatch: {} is of length {}, but length {} is required".format(key, len(self._value_table[key]), length))

    def as_rows(self) -> typing.List[typing.List[sciplot.Value]]:
        """
        Get the variables table (after calling load()) as a list of lists where each list is a table row

        Returns:
            (list of list of Value)
        """
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

    def as_columns(self) -> typing.List[typing.List[sciplot.Value]]: #matches internal layout, simply return
        """
        Get the variables table (after calling load()) as a list of lists where each list is a table column

        Returns:
            (list of list of Value)
        """
        result = []

        for variable_id in self._variable_ids:
            result.append(self._value_table[variable_id])

        return result