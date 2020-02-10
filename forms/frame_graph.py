import wx
import wx.lib.plot.plotcanvas

import forms

import sciplot.database


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
        self._plot_ids = []
        self._variable_ids = []

        self._lb_plots = wx.ListBox(self, wx.ID_ANY)
        self._lb_plots.Bind(wx.EVT_LISTBOX, self._bind_lb_plots_new_selection)
        self._gbs_main.Add(self._lb_plots, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._chk_show_regression = wx.CheckBox(self, wx.ID_ANY, "Show Regression", style = wx.ALIGN_CENTRE_HORIZONTAL)
        self._chk_show_regression.Bind(wx.EVT_CHECKBOX, self._bind_chk_show_regression_changed)
        self._gbs_main.Add(self._chk_show_regression, wx.GBPosition(1, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._btn_new_plot = wx.Button(self, wx.ID_ANY, "Add New")
        self._btn_new_plot.Bind(wx.EVT_BUTTON, self._bind_btn_new_plot_clicked)
        self._gbs_main.Add(self._btn_new_plot, wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove_plot = wx.Button(self, wx.ID_ANY, "Remove")
        self._btn_remove_plot.Bind(wx.EVT_BUTTON, self._bind_btn_remove_plot_clicked)
        self._gbs_main.Add(self._btn_remove_plot, wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lbl_plot_x = wx.StaticText(self, wx.ID_ANY, "x-axis", style = wx.ALIGN_CENTRE_HORIZONTAL)
        self._gbs_main.Add(self._lbl_plot_x, wx.GBPosition(3, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._entry_variable_title_x = wx.TextCtrl(self, wx.ID_ANY)
        self._entry_variable_title_x.Bind(wx.EVT_TEXT, self._bind_entry_variable_title_x_changed)
        self._gbs_main.Add(self._entry_variable_title_x, wx.GBPosition(4, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lb_plot_x = wx.ListBox(self, wx.ID_ANY)
        self._lb_plot_x.Bind(wx.EVT_LISTBOX, self._bind_lb_plot_x_new_selection)
        self._gbs_main.Add(self._lb_plot_x, wx.GBPosition(5, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lbl_plot_y = wx.StaticText(self, wx.ID_ANY, "y-axis", style = wx.ALIGN_CENTRE_HORIZONTAL)
        self._gbs_main.Add(self._lbl_plot_y, wx.GBPosition(3, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._entry_variable_title_y = wx.TextCtrl(self, wx.ID_ANY)
        self._entry_variable_title_y.Bind(wx.EVT_TEXT, self._bind_entry_variable_title_y_changed)
        self._gbs_main.Add(self._entry_variable_title_y, wx.GBPosition(4, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lb_plot_y = wx.ListBox(self, wx.ID_ANY)
        self._lb_plot_y.Bind(wx.EVT_LISTBOX, self._bind_lb_plot_y_new_selection)
        self._gbs_main.Add(self._lb_plot_y, wx.GBPosition(5, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_refresh = wx.Button(self, wx.ID_ANY, "Refresh")
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._bind_btn_refresh_clicked)
        self._gbs_main.Add(self._btn_refresh, wx.GBPosition(6, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._plot_main = wx.lib.plot.plotcanvas.PlotCanvas(self, wx.ID_ANY)
        self._plot_main.enableAxes = True
        data = [[1,5],[2,4],[3,8],[4,3],[5,2]]
        line = wx.lib.plot.PolyLine(data, colour='red', width=1)
        gc = wx.lib.plot.PlotGraphics([line], 'Title', 'x-axis', 'y-axis')
        self._plot_main.Draw(gc)
        self._plot_main.enableAntiAliasing = True
        self._plot_main.enableDrag = True
        self._plot_main.Bind(wx.EVT_MOUSEWHEEL, self._bind_graph_scroll)
        self._gbs_main.Add(self._plot_main, wx.GBPosition(0, 2), wx.GBSpan(6, 1), wx.ALL | wx.EXPAND)

        self._btn_reset_zoom = wx.Button(self, wx.ID_ANY, "Reset Zoom")
        self._btn_reset_zoom.Bind(wx.EVT_BUTTON, self._bind_btn_reset_zoom_clicked)
        self._gbs_main.Add(self._btn_reset_zoom, wx.GBPosition(6, 2), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [2]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [0, 5]:
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
    
    def _bind_btn_reset_zoom_clicked(self, event):
        self._plot_main.Reset()
        event.Skip()
    
    def _bind_btn_refresh_clicked(self, event):
        self.refresh()
        event.Skip()
    
    def _bind_lb_plots_new_selection(self, event):
        self.refresh_variable_selections()
        
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            show_regression, variable_x_title, variable_y_title = self._datafile.query(sciplot.database.Query("SELECT ShowRegression, VariableXTitle, VariableYTitle FROM Plot WHERE PlotID = (?);", [self._plot_ids[selection]], 2))[0]
            self._chk_show_regression.SetValue(bool(show_regression))
            self._entry_variable_title_x.ChangeValue(variable_x_title)
            self._entry_variable_title_y.ChangeValue(variable_y_title)

        event.Skip()
    
    def _bind_btn_new_plot_clicked(self, event):
        if len(self._variable_ids) == 0:
            wx.MessageBox("This file contains no variables\nYou need to create one before you make a plot", "No variables", wx.ICON_ERROR | wx.OK)
        else:
            self._datafile.query(sciplot.database.Query("INSERT INTO Plot (VariableXID, VariableYID, VariableXTitle, VariableYTitle, ShowRegression) VALUES ((?), (?), (?), (?), (?))", [self._variable_ids[0], self._variable_ids[0], "<blank>", "<blank>", 1], 0))

            self.refresh()

        event.Skip()
    
    def _bind_btn_remove_plot_clicked(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            self._datafile.query(sciplot.database.Query("DELETE FROM Plot WHERE PlotID = (?)", [self._plot_ids[selection]], 0))
            self.refresh()
    
        event.Skip()
    
    def _bind_chk_show_regression_changed(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET ShowRegression = (?) WHERE PlotID = (?);", [int(self._chk_show_regression.GetValue()), self._plot_ids[selection]], 0))
        
        event.Skip()
    
    def _bind_lb_plot_x_new_selection(self, event):
        plot_selection = self._lb_plots.GetSelection()
        var_selection = self._lb_plot_x.GetSelection()
        if plot_selection != -1 and var_selection != -1:
            plot_id = self._plot_ids[plot_selection]
            var_id = self._variable_ids[var_selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableXID = (?) WHERE PlotID = (?);", [var_id, plot_id], 0))

        event.Skip()

    def _bind_lb_plot_y_new_selection(self, event):
        plot_selection = self._lb_plots.GetSelection()
        var_selection = self._lb_plot_y.GetSelection()
        if plot_selection != -1 and var_selection != -1:
            plot_id = self._plot_ids[plot_selection]
            var_id = self._variable_ids[var_selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableYID = (?) WHERE PlotID = (?);", [var_id, plot_id], 0))

        event.Skip()
    
    def _bind_entry_variable_title_x_changed(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            plot_id = self._plot_ids[selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableXTitle = (?) WHERE PlotID = (?);", [self._entry_variable_title_x.GetValue(), plot_id], 0))

            self.refresh_plot_titles()

        event.Skip()
    
    def _bind_entry_variable_title_y_changed(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            plot_id = self._plot_ids[selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableYTitle = (?) WHERE PlotID = (?);", [self._entry_variable_title_y.GetValue(), plot_id], 0))

            self.refresh_plot_titles()

        event.Skip()
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh()
    
    def hook_frame_selected(self):
        self.refresh()

    #frame methods
    def refresh(self):
        self.refresh_plot_titles()
        self.refresh_variables()
        self.refresh_variable_selections()
    
    def refresh_plot_titles(self):
        selection = self._lb_plots.GetSelection()

        self._plot_ids.clear()
        self._lb_plots.Clear()

        for plot_id, plot_title_x, plot_title_y in self._datafile.query(sciplot.database.Query("SELECT PlotID, VariableXTitle, VariableYTitle FROM Plot", [], 1))[0]:
            self._lb_plots.Append("{}-{}".format(plot_title_y, plot_title_x))
            self._plot_ids.append(plot_id)
        
        if selection != -1 and len(self._plot_ids) > 0:
            self._lb_plots.SetSelection(min(len(self._plot_ids) - 1, selection))
    
    def refresh_variables(self):
        selection_x = self._lb_plot_x.GetSelection()
        selection_y = self._lb_plot_y.GetSelection()

        self._variable_ids.clear()
        self._lb_plot_x.Clear()
        self._lb_plot_y.Clear()

        for variable_id, variable_symbol in self._datafile.query(sciplot.database.Query("SELECT VariableID, Symbol FROM Variable", [], 1))[0]:
            self._variable_ids.append(variable_id)
            self._lb_plot_x.Append(variable_symbol)
            self._lb_plot_y.Append(variable_symbol)
        
        if len(self._variable_ids) > 0:
            if selection_x != -1:
                self._lb_plot_x.SetSelection(min(len(self._variable_ids) - 1, selection_x))
            
            if selection_y != -1:
                self._lb_plot_y.SetSelection(min(len(self._variable_ids) - 1, selection_y))
    
    def refresh_variable_selections(self):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            plot_x_id, plot_y_id = self._datafile.query(sciplot.database.Query("SELECT VariableXID, VariableYID FROM Plot WHERE PlotID = (?)", [self._plot_ids[selection]], 2))[0]

            self._lb_plot_x.SetSelection(self._variable_ids.index(plot_x_id))
            self._lb_plot_y.SetSelection(self._variable_ids.index(plot_y_id))
        
        else:
            self._lb_plot_x.SetSelection(-1)
            self._lb_plot_y.SetSelection(-1)