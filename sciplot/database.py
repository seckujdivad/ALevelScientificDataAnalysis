from dataclasses import dataclass
import multiprocessing as mp
import sqlite3
import threading
import typing


@dataclass
class Query:
    query: str
    arguments: list
    fetchmode: int #0: fetch none, 1: fetch all, 2: fetch one, 3: fetch many


class Database:
    """
    A thread-safe SQLite3 database object

    Args:
        path (str): the path to the SQLite3 database
    """
    def __init__(self, path: str):
        self._connection: sqlite3.Connection = None

        self._pipe, pipe = mp.Pipe()
        threading.Thread(target = self._queryd, args = [path, pipe], name = 'SQLite3 Database Query Thread', daemon = True).start()

        self._data_output = {}
        self._data_written_event = threading.Event()
        self._data_counter = 0
        self._data_counter_event = threading.Event()
        self._data_counter_event.set()

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
                for line in query.query.splitlines():

                        return_values.append(cursor.fetchall())

                        return_values.append(cursor.fetchone())

                    elif query.fetchmode == 3:
                        return_values.append(cursor.fetchmany())
                
            if len(return_values) > 0:
                self._data_output[counter] = return_values
                self._data_written_event.set()
                self._data_written_event.wait()
        
        self._connection.close()

    def query(self, query: typing.Union[Query, typing.List[Query]]):
        """
        Sends a Query object (or a list of Query objects) to the database. If any Query objects expect a response, hang until one is recieved

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
                if q.fetchmode != 0:
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
                    self._data_written_event.wait() #wait for data to be written

                    if counter in self._data_output: #check if the data that has been written is for this call
                        result = self._data_output.pop(counter)
                        cont = False

                        self._query_thread_release_event.set()

                    self._data_written_event.clear()

            return result

        else:
            return self.query([query]) #don't duplicate functionality, just make another call with a corrected data format
    
    def close(self):
        self._running = False