import typing

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

                else:
                    current_dependency["type"] = "value"

                    if dependency.endswith(".MEAN"):
                        current_dependency["access mode"] = "single"
                        current_dependency["processing"] = "mean"
                    
                    elif dependency.endswith(".MAX"):
                        current_dependency["access mode"] = "single"
                        current_dependency["processing"] = "max"
                    
                    elif dependency.endswith(".MIN"):
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
        #get dataset dependencies
        dataset_table: typing.Dict[str, typing.Union[functions.Value, typing.List[functions.Value]]] = {}
        for dependency_name in dependency_table:
            dependency_data = dependency_table[dependency_name]
            if dependency_data["type"] == "dataset" and dependency_data["subtype"] is None:
                values = [tup[0] for tup in self._datafile.query(database.Query("SELECT `Value` FROM DataPoint INNER JOIN DataSet ON DataPoint.DataSetID = DataSet.DataSetID INNER JOIN `Variable` ON DataSet.DataSetID = Variable.ID WHERE Symbol = (?) AND Type = 0;", [dependency_data["symbol"]], 1))[0]]
                print(dependency_data["symbol"], values)

            elif dependency_data["type"] == "graphical":
                pass

    def as_rows(self):
        if len(self._value_table) > 0: #transpose row-column layout
            result = []
            row = []

            for row_index in range(len(self._value_table[0])):
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