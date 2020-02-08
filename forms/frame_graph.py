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
        self._lb_plots = wx.ListBox(self, wx.ID_ANY)
        self._gbs_main.Add(self._lb_plots, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._entry_plot_name = wx.TextCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._entry_plot_name, wx.GBPosition(1, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._btn_new_plot = wx.Button(self, wx.ID_ANY, "Add New")
        self._gbs_main.Add(self._btn_new_plot, wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove_plot = wx.Button(self, wx.ID_ANY, "Remove")
        self._gbs_main.Add(self._btn_remove_plot, wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lbl_plot_x = wx.StaticText(self, wx.ID_ANY, "x-axis", style = wx.ALIGN_CENTRE_HORIZONTAL)
        self._gbs_main.Add(self._lbl_plot_x, wx.GBPosition(3, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lb_plot_x = wx.ListBox(self, wx.ID_ANY)
        self._gbs_main.Add(self._lb_plot_x, wx.GBPosition(4, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lbl_plot_y = wx.StaticText(self, wx.ID_ANY, "y-axis", style = wx.ALIGN_CENTRE_HORIZONTAL)
        self._gbs_main.Add(self._lbl_plot_y, wx.GBPosition(3, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lb_plot_y = wx.ListBox(self, wx.ID_ANY)
        self._gbs_main.Add(self._lb_plot_y, wx.GBPosition(4, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._plot_main = wx.lib.plot.plotcanvas.PlotCanvas(self, wx.ID_ANY)
        self._plot_main.enableAxes = True
        data = [[1,5],[2,4],[3,8],[4,3],[5,2]]
        line = wx.lib.plot.PolyLine(data, colour='red', width=1)
        gc = wx.lib.plot.PlotGraphics([line], 'Title', 'x-axis', 'y-axis')
        self._plot_main.Draw(gc)
        self._plot_main.enableAntiAliasing = True
        self._plot_main.enableDrag = True
        self._plot_main.Bind(wx.EVT_MOUSEWHEEL, self._bind_graph_scroll)
        self._gbs_main.Add(self._plot_main, wx.GBPosition(0, 2), wx.GBSpan(5, 1), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [2]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [0, 4]:
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
        
        centre = (self._plot_main.xCurrentRange[0] + (self._plot_main.xCurrentRange[1] - self._plot_main.xCurrentRange[0]) / 2,
                  self._plot_main.yCurrentRange[0] + (self._plot_main.yCurrentRange[1] - self._plot_main.yCurrentRange[0]) / 2)

        self._plot_main.Zoom(centre, (zoom, zoom))
        event.Skip()