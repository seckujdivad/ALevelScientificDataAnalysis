import wx
import wx.dataview
import typing


class SubFrame(wx.Panel):
    def __init__(self, parent, root_frame):
        super().__init__(parent, wx.ID_ANY)

        self.root_frame = root_frame
        self.parent = parent

        self.identifier = 'null'
        self.styling_name = '<blank>'
        self.styling_icon = wx.Bitmap('resources/toolbar/blank.bmp')
        self.toolbar_index = -1


class DataFrame(SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'data'
        self.styling_name = 'Data'
        self.styling_icon = wx.Bitmap('resources/toolbar/data.bmp')

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        for i in range(1):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(1):
            self._gbs_main.AddGrowableRow(j)

        #create elements
        self._dvl_data = wx.dataview.DataViewListCtrl(self, wx.ID_ANY)
        self._dvl_columns = []
        self._dvl_columns.append(self._dvl_data.AppendTextColumn("Column 1"))
        self._dvl_columns.append(self._dvl_data.AppendTextColumn("Column 2"))
        self._dvl_data.AppendItem([1, 2])
        self._gbs_main.Add(self._dvl_data, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)
        
        #finalise layout
        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)

        self.SetBackgroundColour('#FFFFFF')


class GraphFrame(SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'graph'
        self.styling_name = 'Graph'
        self.styling_icon = wx.Bitmap('resources/toolbar/graph.bmp')


class TablesFrame(SubFrame):
    pass


class FormulaeFrame(SubFrame):
    pass


class ConstantsFrame(SubFrame):
    pass


manifest: typing.List[SubFrame] = [DataFrame, GraphFrame] #, TablesFrame, FormulaeFrame, ConstantsFrame]