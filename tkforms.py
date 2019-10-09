import tkinter as tk
import abc


class Form(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __del__(self):
        pass
    
    def show(self):
        pass

    def hide(self):
        pass

    @abc.abstractclassmethod
    def _on_show(self):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def _on_hide(self):
        raise NotImplementedError()


class MultiFormViewer(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._forms = []
    
    def add_form(self, form):
        self._forms.append(form)
    
    def remove_form(self, form):
        self._forms.remove(form)