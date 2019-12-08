import wx
import typing


class SubFrame(wx.Panel):
    def __init__(self, parent, root_frame):
        super().__init__(parent, wx.ID_ANY)

        self.root_frame = root_frame
        self.parent = parent

        self.identifier = 'null'
        self.styling_name = '<blank>'
        self.styling_icon = wx.Bitmap('resources/toolbar/blank.bmp')


class DataFrame(SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        self.identifier = 'data'
        self.styling_name = 'Data'
        self.styling_icon = wx.Bitmap('resources/toolbar/data.bmp')

        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self._btn_test = wx.Button(self, wx.ID_ANY, "Test button 2 - data")
        self._gbs_main.Add(self._btn_test, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)

        for i in range(1):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(1):
            self._gbs_main.AddGrowableRow(j)

        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)


class GraphFrame(SubFrame):
    pass


class TablesFrame(SubFrame):
    pass


class FormulaeFrame(SubFrame):
    pass


class ConstantsFrame(SubFrame):
    pass


manifest: typing.List[SubFrame] = [DataFrame] #, GraphFrame, TablesFrame, FormulaeFrame, ConstantsFrame]