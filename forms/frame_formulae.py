import wx

import forms


class FormulaeFrame(forms.SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'formulae'
        self.styling_name = 'Formulae'
        self.styling_icon = wx.Bitmap('resources/toolbar/formulae.bmp')