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
        var_type_lookup = ["dataset", "formula"]

        #get all functions from the database
        function_table: typing.Dict[str, functions.Function] = {}
        function_var_table: typing.Dict[int, functions.Function] = {}
        for variable_id, expression, name in self._datafile.query(database.Query("SELECT VariableID, Expression, Symbol FROM Formula INNER JOIN Variable ON ID = FormulaID AND Type = 1", [], 1))[0]:
            func = functions.Function(expression)
            func.pre_evaluate(constants_table) #optimise functions
            function_table[name] = func
            function_var_table[variable_id] = func
        
        #get data on all columns
        variable_data = []
        for variable_id in self._variable_ids:
            variable_symbol, variable_subid, variable_type = self._datafile.query(database.Query("SELECT Symbol, ID, Type FROM Variable WHERE VariableID = (?);", [variable_id], 2))[0]
            variable_data.append([variable_symbol, variable_subid, variable_type])

        #get formula dependencies
        dependent_datasets = {}
        included_datasets = {}

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