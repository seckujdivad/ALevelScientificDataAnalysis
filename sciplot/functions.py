import abc


#interface defining all functions
class IMathematicalFunction:
    def __init__(self):
        self._subfuncs = []

    @abc.abstractclassmethod
    def evaluate(self, datatable):
        raise NotImplementedError()


#top level parent function - other classes should interact with this
class Function(IMathematicalFunction):
    pass


#sub functions
class Float(IMathematicalFunction):
    def __init__(self):
        super().__init__()