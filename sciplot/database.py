from dataclasses import dataclass
import multiprocessing, multiprocessing.connection
import sqlite3
import threading
import typing


@dataclass
class Query:
    """
    Struct for sending queries to the database thread

    query (str): SQLite query to be executed on the database

    arguments (list of serialisable): arguments to replace (?) in query

    fetchmode (int: 0-3):
        0 - fetch none
        1 - fetch all
        2 - fetch one
        3 - fetch many
       -1 - blank interrupt (used internally)
    """
    query: str
    arguments: list
    fetchmode: int


class Database:
    """
    A thread-safe SQLite3 database object

    Args:
        path (str): the path to the SQLite3 database
    """
    def __init__(self, path: str):
        #database connection
        self._connection: sqlite3.Connection = None

        #query transfer
        self._query_pipe, pipe = multiprocessing.Pipe()
        self._query_pipe_size: int = 0
        self._query_pipe_ready = threading.Event()
        self._query_pipe_ready.clear()

        #data response
        self._response_values = {}
        self._response_written_event = threading.Event()
        self._response_ids = 0
        self._response_id_event = threading.Event()
        self._response_id_event.set()

        self._response_collected_event = threading.Event()

        #successful db connection control
        self._creation_event = threading.Event()
        self._creation_event.clear()
        self._creation_exception = None

        #closing state control
        self._running = True

        #database thread
        self._query_thread = threading.Thread(target = self._queryd, args = [path, pipe], name = 'SQLite3 Database Query Thread', daemon = True)
        self._query_thread.start()

        #throw any database creation exceptions
        self._creation_event.wait()
        if self._creation_exception is not None:
            raise type(self._creation_exception)(str(self._creation_exception))
    
    def _queryd(self, path: str, pipe: multiprocessing.connection.PipeConnection):
        """
        Thread that processes queries and handles interactions with the database. Automatically started on object creation
        """
        try:
            self._connection: sqlite3.Connection = sqlite3.connect(path)
        except Exception as e:
            self._creation_exception = e
        finally:
            self._creation_event.set()

        while self._running:
            self._query_pipe_ready.wait()
            data: typing.Tuple[int, typing.List[Query]] = pipe.recv()
            self._query_pipe_size -= 1
            if self._query_pipe_size <= 0:
                self._query_pipe_ready.clear()
            counter, queries = data

            return_values = []
            for query in queries:
                if query.fetchmode != -1: #blank interrupt, skip this query
                    try:
                        for line in query.query.splitlines():
                            cursor = self._connection.execute(line, query.arguments)

                            if query.fetchmode == 1:
                                return_values.append((0, cursor.fetchall()))

                            elif query.fetchmode == 2:
                                return_values.append((0, cursor.fetchone()))

                            elif query.fetchmode == 3:
                                return_values.append((0, cursor.fetchmany()))
                    
                    except Exception as e:
                        return_values.append((1, (type(e), str(e))))
                        self._running = False
                
            if len(return_values) > 0:
                self._response_values[counter] = return_values
                self._response_collected_event.clear()
                self._response_written_event.set() #release all waiting query calls
                self._response_collected_event.wait() #wait for the data to be claimed by a thread
        
        self._connection.close()
        self._query_pipe.close()
        self._response_collected_event.clear() #release any other waiting threads

    def query(self, query: typing.Union[Query, typing.List[Query]]):
        """
        Sends a Query object (or a list of Query objects) to the database. If any Query objects expect a response, hang until one is received

        Args:
            query (Query or list of Query): Queries to be executed
        
        Returns:
            list of
                tuple: fetchmode = 2
                list of tuple: fetchmode = 1, 3
            for each query where fetchmode =/= 0
        """
        if type(query) == list:
            #check if any of the queries expect a response
            wait_for_value = False
            for q in query:
                if q.fetchmode not in [-1, 0]:
                    wait_for_value = True

            self._response_id_event.wait()
            self._response_id_event.clear()

            self._query_pipe.send((self._response_ids, query))

            self._query_pipe_size += 1
            self._query_pipe_ready.set()

            counter = self._response_ids
            self._response_ids += 1
            self._response_id_event.set()

            result = None

            if wait_for_value: #at least one query expects a value
                cont = True
                while cont and self._running:
                    self._response_written_event.wait() #wait for data to be written
                    
                    if counter in self._response_values: #check if the data that has been written is for this call
                        returned_value = self._response_values.pop(counter)

                        result = []
                        for identifier, data in returned_value:
                            if identifier == 0:
                                result.append(data)
                                
                            elif identifier == 1:
                                raise data[0](data[1]) #exceptions triggered here have been handed down by the database thread

                        cont = False
                        self._response_collected_event.set()

                    self._response_written_event.clear()

            return result

        else:
            return self.query([query]) #don't duplicate functionality, just make another call with a corrected data format
        
    def commit(self, wait: bool = True):
        self.query([Query('COMMIT;', [], int(wait)),
                    Query('BEGIN;', [], int(wait))])
    
    def close(self, wait: bool = True):
        """
        Closes the database and stops all running threads. Doesn't commit the database; this must be done through self.query or self.commit

        Args:
            wait (bool: True): wait for the thread to exit before returning
        """
        if self._running:
            self._running = False

            try:
                self.query(Query("", [], -1)) #interrupt the thread so that it will process _running = False
            except:
                pass #pipe has already been closed

            if wait:
                self._query_thread.join() #wait for the thread to exit
    
    #context management
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


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
        return self.query(query)[0][0]

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

        match_found = False
        i = 0
        while i < len(unitcomposite_ids) and not match_found:
            scan_units = self.query(Query("SELECT UnitCompositeDetails.UnitID, UnitCompositeDetails.Power FROM UnitComposite INNER JOIN UnitCompositeDetails ON UnitCompositeDetails.UnitCompositeID = UnitComposite.UnitCompositeID WHERE UnitComposite.UnitCompositeID = (?);", [unitcomposite_ids[i]], 1))[0]
            
            if set(scan_units) == set(unit_table):
                match_found = True

            i += 1

        if match_found:
            return unitcomposite_ids[i - 1]
        
        else:
            return -1
    
    def rename_unit(self, primary_key: int, symbol: str):
        self.query(Query("UPDATE UnitComposite SET Symbol = (?) WHERE UnitCompositeID = (?);", [symbol, primary_key], 0))
    
    def update_unit(self, primary_key: int, unit_table: typing.List[typing.Tuple[int, float]]):
        queries = [Query("DELETE FROM UnitCompositeDetails WHERE UnitCompositeID = (?)", [primary_key], 0)]
        for unit_id, power in unit_table:
            queries.append(Query("INSERT INTO UnitCompositeDetails (`UnitCompositeID`, `UnitID`, `Power`) VALUES ((?), (?), (?))", [primary_key, unit_id, power], 0))
        self.query(queries)
    
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
                variable_id =self.query(Query('SELECT VariableID FROM Variable WHERE ID = (?) AND Type = (?)', [sub_id, variable_type], 2))[0]

        if remove_plots:
            self.query(Query('DELETE FROM Plot WHERE VariableXID = (?) OR VariableYID = (?)', [variable_id, variable_id], 0))
        
        if remove_columns:
            self.query(Query('DELETE FROM TableColumn WHERE VariableID = (?)', [variable_id], 0))
    
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