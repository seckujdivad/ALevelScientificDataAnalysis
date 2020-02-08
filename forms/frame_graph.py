import wx
import wx.lib.plot.plotcanvas

import forms


class GraphFrame(forms.SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'graph'
        self.styling_name = 'Graph'
        self.styling_icon = wx.Bitmap('resources/toolbar/graph.bmp')

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #create elements
        self._graph_main = wx.lib.plot.plotcanvas.PlotCanvas(self, wx.ID_ANY)
        self._graph_main.enableAxes = True
        data = [[1,5],[2,4],[3,8],[4,3],[5,2]]
        line = wx.lib.plot.PolyLine(data, colour='red', width=1)
        gc = wx.lib.plot.PlotGraphics([line], 'Title', 'x-axis', 'y-axis')
        self._graph_main.Draw(gc)
        self._graph_main.enableAntiAliasing = True
        self._graph_main.enableDrag = True
        self._graph_main.Bind(wx.EVT_MOUSEWHEEL, self._bind_graph_scroll)
        self._gbs_main.Add(self._graph_main, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [0]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [0]:
            self._gbs_main.AddGrowableRow(j)
        
        #finalise layout
        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)
    
    #ui binds
    def _bind_graph_scroll(self, event):
        rotation = event.GetWheelRotation()
        if rotation > 0:
            zoom = 0.9
        else:
            zoom = 1.1
        
        centre = (self._graph_main.xCurrentRange[0] + (self._graph_main.xCurrentRange[1] - self._graph_main.xCurrentRange[0]) / 2,
                  self._graph_main.yCurrentRange[0] + (self._graph_main.yCurrentRange[1] - self._graph_main.yCurrentRange[0]) / 2)

        self._graph_main.Zoom(centre, (zoom, zoom))
        event.Skip()