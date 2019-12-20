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
        self._connection: sqlite3.Connection = sqlite3.connect(path)

        while self._running:
            data: typing.Tuple[int, typing.List[Query]] = pipe.recv()
            counter, queries = data

            return_values = []
            for query in queries:
                cursor = self._connection.execute(query.query, query.arguments)

                if query.fetchmode == 1:
                    return_values.append(cursor.fetchall())

                elif query.fetchmode == 2:
                    return_values.append(cursor.fetchone())

                elif query.fetchmode == 3:
                    return_values.append(cursor.fetchmany())
                
            if len(return_values) > 0:
                self._data_output[counter] = return_values
                self._data_written_event.set()
                self._data_written_event.wait()
        
        self._connection.close()

    def query(self, query: typing.Union[Query, typing.List[Query]]):
        if type(query) == list:
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

            if wait_for_value:
                cont = True
                while cont:
                    self._data_written_event.wait()

                    if counter in self._data_output:
                        result = self._data_output.pop(counter)
                        cont = False

                    self._data_written_event.clear()

            return result

        else:
            return self.query([query])
    
    def close(self):
        self._running = False