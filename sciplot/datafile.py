from sciplot.database import *


class DataFile(Database):
    """
    A thread-safe database object with methods specific to databases following the internal file structure

    Args:
        path (str): path to datafile
    """
    def __init__(self, path: str):
        super().__init__(path)

        query = Query("BEGIN", [], 1)
        self.query(query)
    
    #management
    def create_rollback(self):
        queries = [Query("COMMIT", [], 0), Query("BEGIN", [], 0)]
        self.query(queries)

    def goto_rollback(self):
        query = Query("ROLLBACK", [], 1)
        self.query(query)
    
    #metadata
    def get_metadata(self, key: str):
        result = self.query(Query('SELECT Value FROM Metadata WHERE Key = (?)', [key], 2))
        if result == []:
            return None
        else:
            return result[0][0]
    
    def set_metadata(self, key: str, value: str):
        self.query([Query('DELETE FROM Metadata WHERE Key = (?)', [key], 0),
                    Query('INSERT INTO Metadata VALUES ((?), (?))', [key, value], 0)])
    
    def list_metadata(self):
        return self.query(Query('SELECT * FROM Metadata', [], 1))[0]
    
    def remove_metadata(self, key: str):
        self.query(Query('DELETE FROM Metadata WHERE Key = (?)', [key], 0))

    #constants
    def list_constants(self):
        query = Query("SELECT Value, Symbol FROM Constant ORDER BY Symbol DESC", [], 1)
        result = self.query(query)
        return result[0]

    def create_constant(self, name: str, value: float, unit_id: int):
        queries = [Query('INSERT INTO Constant (UnitCompositeID, Value, Symbol) VALUES ((?), (?), (?));', [unit_id, value, name], 0),
                   Query('SELECT last_insert_rowid();', [], 2)]
        return self.query(queries)[0][0]

    def get_constant(self, name: str):
        query = Query("SELECT ConstantID, Value, UnitCompositeID FROM Constant WHERE Symbol = (?)", [name], 2)
        return self.query(query)[0]

    def get_constant_by_id(self, constant_id: int):
        query = Query("SELECT Symbol, Value, UnitCompositeID FROM Constant WHERE ConstantID = (?)", [constant_id], 2)
        return self.query(query)[0]
    
    def remove_constant(self, constant_id: int):
        self.query(Query('DELETE FROM Constant WHERE ConstantID = (?)', [constant_id], 0))

    #base SI units
    def list_base_units(self):
        query = Query("SELECT * FROM Unit", [], 1)
        result = self.query(query)
        return result[0]
    
    def get_base_unit(self, base_unit_id: int):
        query = Query("SELECT Symbol FROM Unit WHERE UnitID = (?)", [base_unit_id], 2)
        return self.query(query)[0][0]
    
    #composite units
    def get_unit_id_by_symbol(self, symbol: str):
        query = Query("SELECT UnitCompositeID FROM UnitComposite WHERE Symbol = (?)", [symbol], 2)
        return [tup[0] for tup in self.query(query)]

    def get_unit_by_id(self, unit_id: int):
        unit_details = self.query(Query("SELECT Unit.UnitID, UnitCompositeDetails.Power FROM UnitCompositeDetails INNER JOIN Unit ON Unit.UnitID = UnitCompositeDetails.UnitID WHERE UnitCompositeDetails.UnitCompositeID = (?)", [unit_id], 1))[0]
        unit_symbol = self.query(Query('SELECT UnitComposite.Symbol FROM UnitComposite WHERE UnitComposite.UnitCompositeID = (?)', [unit_id], 2))[0][0]
        return unit_symbol, unit_details
    
    def create_unit(self, symbol: str, base_units: typing.List[typing.Tuple[int, float]]):
        queries = [Query('INSERT INTO UnitComposite (Symbol) VALUES ((?));', [symbol], 0),
                   Query("SELECT last_insert_rowid();", [], 2)]
        unit_id = self.query(queries)[0][0]

        for base_unit_id, power in base_units:
            query = Query('INSERT INTO UnitCompositeDetails (UnitCompositeID, UnitID, Power) VALUES ((?), (?), (?))', [unit_id, base_unit_id, power], 0)
            self.query(query)
            
        return unit_id
    
    def list_units(self):
        return [val[0] for val in self.query(Query('SELECT UnitCompositeID FROM UnitComposite;', [], 1))[0]] #unpack tuples
    
    def remove_unit(self, unit_id: int):
        self.query([Query('DELETE FROM UnitComposite WHERE UnitCompositeID = (?)', [unit_id], 0),
                    Query('DELETE FROM UnitCompositeDetails WHERE UnitCompositeID = (?)', [unit_id], 0)])
    
    def get_unit_id_by_table(self, unit_table: typing.List[typing.Tuple[int, float]]):
        unitcomposite_ids = [tup[0] for tup in self.query(Query("SELECT UnitCompositeID FROM UnitComposite;", [], 1))[0]]

        matches = []
        i = 0
        while i < len(unitcomposite_ids):
            scan_units = self.query(Query("SELECT UnitCompositeDetails.UnitID, UnitCompositeDetails.Power FROM UnitComposite INNER JOIN UnitCompositeDetails ON UnitCompositeDetails.UnitCompositeID = UnitComposite.UnitCompositeID WHERE UnitComposite.UnitCompositeID = (?);", [unitcomposite_ids[i]], 1))[0]
            
            if set(scan_units) == set(unit_table):
                matches.append(unitcomposite_ids[i])

            i += 1

        return matches
    
    def rename_unit(self, primary_key: int, symbol: str):
        self.query(Query("UPDATE UnitComposite SET Symbol = (?) WHERE UnitCompositeID = (?);", [symbol, primary_key], 0))
    
    def update_unit(self, primary_key: int, unit_table: typing.List[typing.Tuple[int, float]]):
        queries = [Query("DELETE FROM UnitCompositeDetails WHERE UnitCompositeID = (?)", [primary_key], 0)]
        for unit_id, power in unit_table:
            queries.append(Query("INSERT INTO UnitCompositeDetails (`UnitCompositeID`, `UnitID`, `Power`) VALUES ((?), (?), (?))", [primary_key, unit_id, power], 0))
        self.query(queries)
    
    def update_units(self, table_name: str, table_id: int, unit_name: str, unit_table: typing.List[typing.Tuple[int, float]]):
        if table_name not in ["DataSet", "Constant"]: #sanitise input
            raise ValueError('Invalid table: {}'.format(table_name))

        unit_composite_id = self.query(Query("SELECT UnitCompositeID FROM {0} WHERE {0}ID = (?);".format(table_name), [table_id], 2))[0][0]

        #remove 0 powers
        for tup in unit_table:
            if tup[1] == 0:
                unit_table.remove(tup)

        units_changed = False
        if self.query(Query("SELECT Symbol FROM UnitComposite WHERE UnitCompositeID = (?);", [unit_composite_id], 2))[0][0] != unit_name:
            units_changed = True
        if set(self.get_unit_by_id(unit_composite_id)[1]) != set(unit_table):
            units_changed = True
        
        if units_changed: #merge/split/edit current composite units
            references = [tup[0] for tup in self.query(Query("SELECT {0}ID FROM {0} WHERE UnitCompositeID = (?);".format(table_name), [unit_composite_id], 1))[0]]

            if len(references) > 1:
                new_composite_id = self.create_unit(unit_name, unit_table)
                self.query(Query("UPDATE {0} SET UnitCompositeID = (?) WHERE {0}ID = (?);".format(table_name), [new_composite_id, table_id], 0))

            else:
                shared_units = self.get_unit_id_by_table(unit_table)

                potential_merges = []
                for unit_id in shared_units:
                    if self.get_unit_by_id(unit_id)[0] == unit_name and unit_id != unit_composite_id:
                        potential_merges.append(unit_id)
                
                if len(potential_merges) == 0:
                    self.rename_unit(unit_composite_id, unit_name)
                    self.update_unit(unit_composite_id, unit_table)
                else:
                    self.query(Query("UPDATE {0} SET UnitCompositeID = (?) WHERE {0}ID = (?);".format(table_name), [potential_merges[0], table_id], 0))
                    self.query(Query("DELETE FROM UnitComposite WHERE UnitCompositeID = (?);", [unit_composite_id], 0))
                    self.query(Query("DELETE FROM UnitCompositeDetails WHERE UnitCompositeID = (?);", [unit_composite_id], 0))
    
    def prune_unused_composite_units(self):
        for composite_unit_id in self.query(Query("SELECT UnitCompositeID FROM UnitComposite", [], 1))[0]:
            composite_unit_id = composite_unit_id[0]

            if len(self.query(Query("SELECT DataSetID FROM DataSet WHERE UnitCompositeID = (?)", [composite_unit_id], 1))[0]) == 0 and len(self.query(Query("SELECT ConstantID FROM Constant WHERE UnitCompositeID = (?)", [composite_unit_id], 1))[0]) == 0:
                self.query(Query("DELETE FROM UnitComposite WHERE UnitCompositeID = (?);", [composite_unit_id], 1))
                self.query(Query("DELETE FROM UnitCompositeDetails WHERE UnitCompositeID = (?);", [composite_unit_id], 1))
    
    #data sets
    def list_data_sets(self):
        return [tup[0] for tup in self.query(Query('SELECT DataSetID FROM DataSet', [], 1))[0]]
    
    def get_data_set(self, data_set_id: int):
        query = '''SELECT DataSet.UnitCompositeID, DataSet.Uncertainty, DataSet.UncIsPerc FROM DataSet
WHERE DataSet.DataSetID = (?)'''
        return self.query(Query(query.replace('\n', ' '), [data_set_id], 2))[0]
    
    def create_data_set(self, uncertainty: float, is_percentage: bool, unit_id: int):
        if is_percentage:
            isperc = 1
        else:
            isperc = 0

        queries = [Query('INSERT INTO DataSet (UnitCompositeID, Uncertainty, UncIsPerc) VALUES ((?), (?), (?));', [unit_id, uncertainty, isperc], 0),
                   Query('SELECT last_insert_rowid();', [], 2)]
        return self.query(queries)[0][0]
    
    def remove_data_set(self, data_set_id: int):
        self.remove_variable(data_set_id = data_set_id, remove_plots = False, remove_columns = False)
    
    #data points
    def get_data_points(self, data_set_id: int):
        return self.query(Query('SELECT DataPointID, Value FROM DataPoint WHERE DataSetID = (?);', [data_set_id], 1))[0]
    
    def remove_data_point(self, data_point_id: int):
        self.query(Query('DELETE FROM DataPoint WHERE DataPointID = (?)', [data_point_id], 0))
    
    def create_data_point(self, value: float, data_set_id: int):
        return self.query([Query('INSERT INTO DataPoint (DataSetID, Value) VALUES ((?), (?));', [data_set_id, value], 0),
                           Query('SELECT last_insert_rowid();', [], 2)])[0][0]
    
    def get_data_point(self, data_point_id: int):
        return self.query(Query('SELECT DataSetID, Value FROM DataPoint WHERE DataPointID = (?)', [data_point_id], 2))[0]
    
    #formulae
    def list_formulae(self):
        return [tup[0] for tup in self.query(Query('SELECT FormulaID FROM Formula', [], 1))[0]]
    
    def get_formula(self, formula_id: int):
        return self.query(Query('SELECT Expression FROM Formula WHERE FormulaID = (?)', [formula_id], 2))[0][0]
    
    def create_formula(self, expression: str):
        return self.query([Query('INSERT INTO Formula (Expression) VALUES ((?))', [expression], 0),
                           Query('SELECT last_insert_rowid();', [], 2)])[0][0]
    
    def remove_formula(self, formula_id: int):
        self.remove_variable(formula_id = formula_id, remove_plots = False, remove_columns = False)
    
    #variables
    def list_variables(self):
        return self.query(Query('SELECT VariableID FROM Variable', [], 1))[0]
    
    def get_variable(self, variable_id: int):
        return self.query(Query('SELECT Symbol, Type, ID FROM Variable WHERE VariableID = (?)', [variable_id], 2))[0]
    
    def create_variable(self, symbol: int, type: int, type_id: int): #0: data set, 1: formula
        return self.query([Query('INSERT INTO Variable (Symbol, Type, ID) VALUES ((?), (?), (?))', [symbol, type, type_id], 0),
                           Query('SELECT last_insert_rowid();', [], 2)])[0]
    
    def remove_variable(self, variable_id: int = -1, formula_id: int = -1, data_set_id: int = -1, remove_plots: bool = True, remove_columns: bool = True, remove_source: bool = True):
        if variable_id != -1:
            variable_type, sub_id = self.query(Query('SELECT Type, ID FROM Variable WHERE VariableID = (?)', [variable_id], 2))[0]
        
        elif data_set_id != -1:
            variable_type = 0
            sub_id = data_set_id

        elif formula_id != -1:
            variable_type = 1
            sub_id = formula_id
        
        else:
            raise ValueError('One of variable_id, formula_id or data_set_id mustn\'t be -1')
        
        if remove_source:
            if variable_type == 0:
                self.query([Query('DELETE FROM DataSet WHERE DataSetID = (?)', [sub_id], 0),
                            Query('DELETE FROM DataPoint WHERE DataSetID = (?)', [sub_id], 0)])
            
            else:
                self.query(Query('DELETE FROM Formula WHERE FormulaID = (?)', [sub_id], 0))
        
        if variable_id == -1:
            if remove_plots or remove_columns:
                variable_id = self.query(Query('SELECT VariableID FROM Variable WHERE ID = (?) AND Type = (?)', [sub_id, variable_type], 2))[0]

        if remove_plots:
            self.query(Query('DELETE FROM Plot WHERE VariableXID = (?) OR VariableYID = (?)', [variable_id, variable_id], 0))
        
        if remove_columns:
            self.query(Query('DELETE FROM TableColumn WHERE VariableID = (?)', [variable_id], 0))
        
        if variable_id == -1:
            self.query(Query("DELETE FROM Variable WHERE ID = (?) AND Type = (?);", [sub_id, variable_type], 0))
        else:
            self.query(Query("DELETE FROM Variable WHERE VariableID = (?);", [variable_id], 0))
    
    #tables
    def list_tables(self):
        return self.query(Query('SELECT * FROM `Table`;', [], 1))[0]
    
    def remove_table(self, table_id: int):
        self.query([Query('DELETE FROM `Table` WHERE TableID = (?)', [table_id], 0),
                    Query('DELETE FROM TableColumn WHERE TableID = (?)', [table_id], 0)])
    
    def create_table(self, title: str):
        return self.query([Query('INSERT INTO `Table` (Title) VALUES ((?))', [title], 0),
                           Query('SELECT last_insert_rowid();', [], 2)])[0][0]
    
    #table columns
    def list_table_columns(self, table_id: int):
        return self.query(Query('SELECT VariableID, FormatPattern FROM TableColumn WHERE TableID = (?)', [table_id], 1))[0]
    
    def create_table_column(self, table_id: int, variable_id: int, format_pattern: str):
        num_matches = len(self.query(Query('SELECT TableID FROM TableColumn WHERE TableID = (?) AND VariableID = (?)', [table_id, variable_id], 1))[0])
        if num_matches > 0:
            raise sqlite3.OperationalError('Duplicate TableID-VariableID pairs are not allowed')

        return self.query([Query('INSERT INTO TableColumn (TableID, VariableID, FormatPattern) VALUES ((?), (?), (?));', [table_id, variable_id, format_pattern], 0),
                           Query('SELECT last_insert_rowid();', [], 2)])[0][0]
    
    def remove_table_column(self, table_id: int, variable_id: int):
        self.query(Query('DELETE FROM TableColumn WHERE TableID = (?) AND VariableID = (?)', [table_id, variable_id], 0))
    
    #plots
    def list_plots(self):
        return [tup[0] for tup in self.query(Query('SELECT PlotID FROM Plot', [], 1))[0]]

    def create_plot(self, variable_x_id: int, variable_x_title: str, variable_y_id: int, variable_y_title: str, show_regression: bool = True):
        if show_regression:
            showregress = 1
        else:
            showregress = 0

        return self.query([Query('INSERT INTO Plot (VariableXID, VariableYID, VariableXTitle, VariableYTitle, ShowRegression) VALUES ((?), (?), (?), (?), (?))', [variable_x_id, variable_y_id, variable_x_title, variable_y_title, showregress], 0),
                           Query('SELECT last_insert_rowid()', [], 2)])[0][0]

    def remove_plot(self, plot_id: int):
        self.query(Query('DELETE FROM Plot WHERE PlotID = (?)', [plot_id], 0))
    
    def get_unit_string(self, unit_table: typing.List[typing.Tuple[int, float]]):
        unit_string = ""
        for unit_id, unit_power in unit_table:
            if unit_power != 0:
                unit_name = self.get_base_unit(unit_id)

                if type(unit_power) == float:
                    if unit_power.is_integer():
                        unit_power = int(unit_power)

                if unit_power == 1:
                    unit_string += ' {}'.format(unit_name)
                else:
                    unit_string += ' {}^{}'.format(unit_name, unit_power)
        
        return unit_string[1:]

def create_blank_datafile(path):
    shutil.copyfile("resources/template.db", path)