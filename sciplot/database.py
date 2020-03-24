from dataclasses import dataclass
import multiprocessing, multiprocessing.connection
import sqlite3
import threading
import typing
import shutil


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
                        for line in query.query.split(';'):
                            if line != '':
                                line += ';'
                                
                                cursor = self._connection.execute(line, query.arguments)

                                if query.fetchmode == 1: #mode: fetch all
                                    return_values.append((0, cursor.fetchall()))

                                elif query.fetchmode == 2: #mode: fetch one
                                    return_values.append((0, cursor.fetchone()))

                                elif query.fetchmode == 3: #mode: fetch many rows (unused)
                                    return_values.append((0, cursor.fetchmany()))
                    
                    except Exception as e:
                        if query.fetchmode == 0: #rethrow the exception: there is no thread to throw it in other than this one
                            raise type(e)(str(e))
                        
                        else: #send the exception back to the waiting thread to be thrown there
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
        """
        Commit transaction to the database and open a new one
        """
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
    #these python magic methods allow it to be used in with .. as ..: syntax where the database is guaranteed to be closed automatically
    #magic methods are similar to operator overloading in cpp
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()