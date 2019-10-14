import tkinter as tk
import abc


class Form(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root = args[0]
    
    def __del__(self):
        pass
    
    def show(self):
        self._on_show()
        self.pack(self.root)

    def hide(self):
        self._on_hide()
        self.pack_forget()

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
        self._current_form = None
    
    def add_form(self, form):
        if isinstance(form, Form):
            self._forms.append(form)
            return len(self._forms) - 1
        
        else:
            raise TypeError('"form" must be of type Form, not {}'.format(type(form)))
    
    def remove_form(self, form):
        if type(form) == int:
            self._forms.pop(form)

        elif isinstance(form, Form):
            self._forms.remove(form)
        
        else:
            raise TypeError('"form" must be of type Form or int, not {}'.format(type(form)))
    
    def switch_to_form(self, index):
        if self._current_form is not None:
            self._forms[self._current_form].hide()

        self._forms[index].show()
        self._current_form = index