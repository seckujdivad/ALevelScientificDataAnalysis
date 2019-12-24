from dataclasses import dataclass
import multiprocessing as mp
import sqlite3
import threading
import typing


@dataclass
class Query:
    query: str
    arguments: list
    fetchmode: int #0: fetch none, 1: fetch all, 2: fetch one, 3: fetch many, -1: blank interrupt (used internally)


class Database:
    """
    A thread-safe SQLite3 database object

    Args:
        path (str): the path to the SQLite3 database
    """
    def __init__(self, path: str):
        self._connection: sqlite3.Connection = None

        self._pipe, pipe = mp.Pipe()
        self._query_thread = threading.Thread(target = self._queryd, args = [path, pipe], name = 'SQLite3 Database Query Thread', daemon = True)
        self._query_thread.start()

        self._data_output = {}
        self._data_written_event = threading.Event()
        self._data_counter = 0
        self._data_counter_event = threading.Event()
        self._data_counter_event.set()
        self._query_thread_release_event = threading.Event()

        self._running = True
    
    def _queryd(self, path: str, pipe):
        """
        Thread that processes queries and handles interactions with the database. Automatically started on object creation
        """
        self._connection: sqlite3.Connection = sqlite3.connect(path)

        while self._running:
            data: typing.Tuple[int, typing.List[Query]] = pipe.recv()
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

                    except sqlite3.OperationalError as e:
                        return_values.append((1, ("OperationalError", str(e))))
                        self._running = False
                
            if len(return_values) > 0:
                self._data_output[counter] = return_values
                self._query_thread_release_event.clear()
                self._data_written_event.set() #release all waiting query calls
                self._query_thread_release_event.wait() #wait for the data to be claimed by a thread
        
        self._connection.close()
        self._query_thread_release_event.clear() #release any other waiting threads

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

            self._data_counter_event.wait()
            self._data_counter_event.clear()
            self._pipe.send((self._data_counter, query))
            counter = self._data_counter
            self._data_counter += 1
            self._data_counter_event.set()

            result = None

            if wait_for_value: #at least one query expects a value
                cont = True
                while cont:
                    if self._running: #don't block if the database thread has stopped
                        self._data_written_event.wait() #wait for data to be written
                    else:
                        cont = False

                    if self._running: #don't block if the database thread has stopped
                        if counter in self._data_output: #check if the data that has been written is for this call
                            returned_value = self._data_output.pop(counter)
                            result = []
                            for identifier, data in returned_value:
                                if identifier == 0:
                                    result.append(data)
                                
                                elif identifier == 1:
                                    if data[0] == "OperationalError":
                                        raise sqlite3.OperationalError(data[1])

                            cont = False
                            self._query_thread_release_event.set()

                        self._data_written_event.clear()
                    else:
                        cont = False

            return result

        else:
            return self.query([query]) #don't duplicate functionality, just make another call with a corrected data format
    
    def close(self, wait = True):
        """
        Closes the database and stops all running threads. Doesn't commit the database; this must be done through self.query

        Args:
            wait (bool: True): wait for the thread to exit before returning
        """
        if self._running:
            self._running = False

            self.query(Query("", [], -1)) #interrupt the thread so that it will process _running = False

            if wait:
                self._query_thread.join() #wait for the thread to exit


class DataFile(Database):
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

    #constants
    def list_constants(self):
        query = Query("SELECT Value, Symbol FROM Constant ORDER BY Symbol DESC", [], 1)
        result = self.query(query)
        return result[0]

    def add_constant(self, name: str, value: float, unit_id: int):
        query = Query("INSERT INTO Constant (UnitCompositeID, Value, Symbol) VALUES ((?), (?), (?)", [unit_id, value, name], 0)
        self.query(query)

    def get_constant(self, name: str):
        query = Query("SELECT ConstantID UnitCompositeID, Value FROM Constant WHERE Symbol = (?)", [name], 2)
        return self.query(query)[0]

    def get_constant_by_id(self, constant_id: int):
        query = Query("SELECT UnitCompositeID, Value, Symbol FROM Constant WHERE ConstantID = (?)", [constant_id], 2)
        return self.query(query)[0]

    #base SI units
    def list_base_units(self):
        query = Query("SELECT * FROM Unit", [], 1)
        result = self.query(query)
        return result[0]
    
    def get_base_unit(self, primary_key: int):
        query = Query("SELECT Symbol FROM Unit WHERE UnitID = (?)", [primary_key], 2)
        return self.query(query)[0][0]
    
    #composite units
    def get_unit(self, symbol: str):
        query = Query("SELECT UnitCompositeID FROM UnitComposite WHERE Symbol = (?)", [symbol], 2)
        return self.get_unit_by_id(self.query(query)[0][0])

    def get_unit_by_id(self, primary_key: int):
        query = Query("SELECT Unit.UnitID Unit.Symbol, UnitCompositeDetails.Power FROM UnitCompositeDetails INNER JOIN Unit ON Unit.UnitID = UnitCompositeDetails.UnitID WHERE UnitCompositeDetails.UnitCompositeID = (?)", [primary_key], 1)
        return self.query(query)[0]
    
    def create_unit(self, symbol: str, base_units: typing.List[typing.Tuple[int, float]]):
        queries = [Query('INSERT INTO UnitComposite (Symbol) VALUES ((?))', [symbol], 0),
                   Query("SELECT last_insert_rowid()", [], 2)]
        unit_id = self.query(queries)[0][0]

        for base_unit_id, power in base_units:
            query = Query('INSERT INTO UnitCompositeDetails (UnitCompositeID, UnitID, Power) VALUES ((?), (?), (?))', [unit_id, base_unit_id, power], 0)
            self.query(query)
            
        return unit_id