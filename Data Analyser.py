import tkforms


class MainForm(tkforms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _on_show(self):
        self.root.title('Data Analyser')

    def _on_hide(self):
        pass


class GraphingForm(tkforms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _on_show(self):
        pass

    def _on_hide(self):
        pass


class DataForm(tkforms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _on_show(self):
        pass

    def _on_hide(self):
        pass


if __name__ == '__main__':
    app = tkforms.App(form = MainForm)