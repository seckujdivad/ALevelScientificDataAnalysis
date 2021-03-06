import wx
import wx.lib.plot.plotcanvas

import forms

import sciplot.database
import sciplot.datafile
import sciplot.graphing


class GraphFrame(forms.SubFrame):
    """
    UI frame for displaying graphs of variables against each other
    """
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
        self._plot_ids = [] #list of primary keys of plots
        self._variable_ids = [] #list of primary keys of variables

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
        self._plot_main.enableAxes = True #display the axes on the graph
        self._plot_main.enableAntiAliasing = True #smoother fit lines
        self._plot_main.enableDrag = True #allow the user to reposition the graph with their mouse
        self._plot_main.useScientificNotation = True #exponential form on axes
        self._plot_main.Bind(wx.EVT_MOUSEWHEEL, self._bind_graph_scroll) #allow the user to scroll to zoom
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
        rotation = event.GetWheelRotation() #get which way the mouse wheel is moving to determine whether to zoom in or out
        if rotation > 0:
            zoom = 0.9
        else:
            zoom = 1 / 0.9
        
        #zoom based on the centre of the screen
        centre = (self._plot_main.xCurrentRange[0] + (self._plot_main.xCurrentRange[1] - self._plot_main.xCurrentRange[0]) / 2,
                  self._plot_main.yCurrentRange[0] + (self._plot_main.yCurrentRange[1] - self._plot_main.yCurrentRange[0]) / 2)

        self._plot_main.Zoom(centre, (zoom, zoom))
        event.Skip()
    
    def _bind_btn_reset_zoom_clicked(self, event):
        self._plot_main.Reset() #resets the plot zoom to the default (plot fills the window exactly)
        event.Skip()
    
    def _bind_btn_refresh_clicked(self, event):
        self.refresh()
        event.Skip()
    
    def _bind_lb_plots_new_selection(self, event):
        self.refresh_variable_selections()
        
        selection = self._lb_plots.GetSelection()
        if selection != -1: #new plot selected (not just changing to no plot selected), so get the plot info and display it in the UI
            show_regression, variable_x_title, variable_y_title = self._datafile.query(sciplot.database.Query("SELECT ShowRegression, VariableXTitle, VariableYTitle FROM Plot WHERE PlotID = (?);", [self._plot_ids[selection]], 2))[0]
            self._chk_show_regression.SetValue(bool(show_regression))
            self._entry_variable_title_x.ChangeValue(variable_x_title)
            self._entry_variable_title_y.ChangeValue(variable_y_title)

        event.Skip()
    
    def _bind_btn_new_plot_clicked(self, event):
        if len(self._variable_ids) == 0: #a variable is required for a plot. the default is the first variable, but if there is no variable to use then the plot can't be made
            wx.MessageBox("This file contains no variables\nYou need to create one before you make a plot", "No variables", wx.ICON_ERROR | wx.OK)
        else:
            self._datafile.query(sciplot.database.Query("INSERT INTO Plot (VariableXID, VariableYID, VariableXTitle, VariableYTitle, ShowRegression) VALUES ((?), (?), (?), (?), (?))", [self._variable_ids[0], self._variable_ids[0], "<blank>", "<blank>", 1], 0))

            self.refresh() #update all UI components

        event.Skip()
    
    def _bind_btn_remove_plot_clicked(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            self._datafile.query(sciplot.database.Query("DELETE FROM Plot WHERE PlotID = (?)", [self._plot_ids[selection]], 0)) #remove the selected plot
            self.refresh()
    
        event.Skip()
    
    def _bind_chk_show_regression_changed(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET ShowRegression = (?) WHERE PlotID = (?);", [int(self._chk_show_regression.GetValue()), self._plot_ids[selection]], 0)) #update the database with the new regression setting for this graph
            self.refresh_plot()
        
        event.Skip()
    
    def _bind_lb_plot_x_new_selection(self, event):
        plot_selection = self._lb_plots.GetSelection()
        var_selection = self._lb_plot_x.GetSelection()
        if plot_selection != -1 and var_selection != -1:
            plot_id = self._plot_ids[plot_selection]
            var_id = self._variable_ids[var_selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableXID = (?) WHERE PlotID = (?);", [var_id, plot_id], 0)) #update the plot with the new x-axis variable

            self.refresh_plot()

        event.Skip()

    def _bind_lb_plot_y_new_selection(self, event):
        plot_selection = self._lb_plots.GetSelection()
        var_selection = self._lb_plot_y.GetSelection()
        if plot_selection != -1 and var_selection != -1:
            plot_id = self._plot_ids[plot_selection]
            var_id = self._variable_ids[var_selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableYID = (?) WHERE PlotID = (?);", [var_id, plot_id], 0)) #update the plot with the new y-axis variable

            self.refresh_plot()

        event.Skip()
    
    def _bind_entry_variable_title_x_changed(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            plot_id = self._plot_ids[selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableXTitle = (?) WHERE PlotID = (?);", [self._entry_variable_title_x.GetValue(), plot_id], 0)) #update the plot with the new x-axis title

            self.refresh_plot_titles()

        event.Skip()
    
    def _bind_entry_variable_title_y_changed(self, event):
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            plot_id = self._plot_ids[selection]
            self._datafile.query(sciplot.database.Query("UPDATE Plot SET VariableYTitle = (?) WHERE PlotID = (?);", [self._entry_variable_title_y.GetValue(), plot_id], 0)) #update the plot with the new y-axis title

            self.refresh_plot_titles()

        event.Skip()
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh()
    
    def hook_frame_selected(self):
        self.refresh()

    #frame methods
    def refresh(self):
        """
        Update all UI elements
        """
        self.refresh_plot_titles()
        self.refresh_variables()
        self.refresh_variable_selections()
        self.refresh_plot()
    
    def refresh_plot_titles(self):
        """
        Update the list of plots in the sidebar from the database
        """
        selection = self._lb_plots.GetSelection()

        self._plot_ids.clear()
        self._lb_plots.Clear()

        for plot_id, plot_title_x, plot_title_y in self._datafile.query(sciplot.database.Query("SELECT PlotID, VariableXTitle, VariableYTitle FROM Plot", [], 1))[0]:
            self._lb_plots.Append("{}-{}".format(plot_title_y, plot_title_x))
            self._plot_ids.append(plot_id)
        
        if selection != -1 and len(self._plot_ids) > 0: #reselect the previous plot if possible, select the last one if not (and don't select anything if there is nothing to select)
            self._lb_plots.SetSelection(min(len(self._plot_ids) - 1, selection))
    
    def refresh_variables(self):
        """
        Update the list of variables that can be used to plot in the sidebar from the database
        """
        selection_x = self._lb_plot_x.GetSelection()
        selection_y = self._lb_plot_y.GetSelection()

        self._variable_ids.clear()
        self._lb_plot_x.Clear()
        self._lb_plot_y.Clear()

        for variable_id, variable_symbol in self._datafile.query(sciplot.database.Query("SELECT VariableID, Symbol FROM Variable", [], 1))[0]: #get all variables from the database
            self._variable_ids.append(variable_id)
            self._lb_plot_x.Append(variable_symbol)
            self._lb_plot_y.Append(variable_symbol)
        
        if len(self._variable_ids) > 0: #try to preserve the previous variable selections
            if selection_x != -1:
                self._lb_plot_x.SetSelection(min(len(self._variable_ids) - 1, selection_x))
            
            if selection_y != -1:
                self._lb_plot_y.SetSelection(min(len(self._variable_ids) - 1, selection_y))
    
    def refresh_variable_selections(self):
        """
        Select the variables used by the current plot in the UI
        """
        selection = self._lb_plots.GetSelection()
        if selection != -1:
            plot_x_id, plot_y_id = self._datafile.query(sciplot.database.Query("SELECT VariableXID, VariableYID FROM Plot WHERE PlotID = (?)", [self._plot_ids[selection]], 2))[0]

            self._lb_plot_x.SetSelection(self._variable_ids.index(plot_x_id))
            self._lb_plot_y.SetSelection(self._variable_ids.index(plot_y_id))

            self.refresh_plot()
        
        else: #no plot is selected, so it doesn't make sense to select variables
            self._lb_plot_x.SetSelection(-1)
            self._lb_plot_y.SetSelection(-1)
    
    def refresh_plot(self):
        """
        Redraw currently selected graph on screen
        """
        self._plot_main.Clear()

        selection = self._lb_plots.GetSelection()
        if selection != -1:
            plot_id = self._plot_ids[selection]
            x_axis_id, y_axis_id, x_axis_title, y_axis_title, show_regression = self._datafile.query(sciplot.database.Query("SELECT VariableXID, VariableYID, VariableXTitle, VariableYTitle, ShowRegression FROM Plot WHERE PlotID = (?)", [plot_id], 2))[0] #get graph data

            lines, x_value, y_value = self.get_plot_lines(x_axis_id, y_axis_id, show_regression) #get data required for drawing currently selected plot

            if lines is not None:
                #add units to axis titles
                x_unit_string = self._datafile.get_unit_string(x_value.units)
                if x_unit_string != '':
                    x_axis_title += ' ({})'.format(x_unit_string)
                
                y_unit_string = self._datafile.get_unit_string(y_value.units)
                if y_unit_string != '':
                    y_axis_title += ' ({})'.format(y_unit_string)
                
                gc = wx.lib.plot.PlotGraphics(lines, 'Plot of {} against {}'.format(y_axis_title, x_axis_title), x_axis_title, y_axis_title) #make a new plot
                self._plot_main.Draw(gc)

    def get_plot_lines(self, x_axis_id, y_axis_id, show_regression = True):
        """
        Get the line objects that make up the plot (points, error bars, fit lines)
        """
        lines = []

        #get constants
        constants_table = {}
        for composite_unit_id, constant_symbol, constant_value in self._datafile.query(sciplot.database.Query("SELECT UnitCompositeID, Symbol, Value FROM Constant;", [], 1))[0]:
            value = sciplot.functions.Value(constant_value)
            if composite_unit_id != None:
                value.units = self._datafile.get_unit_by_id(composite_unit_id)[1]
            constants_table[constant_symbol] = constant_value

        #plot all values
        datatable = sciplot.datatable.Datatable(self._datafile)
        datatable.set_variables([x_axis_id, y_axis_id])

        no_exception = True
        try:
            datatable.load(constants_table) #load data for plotting
        
        except Exception as e:
            wx.MessageBox('Couldn\'t generate values for plotting\n{}'.format(str(e)), type(e).__name__, wx.ICON_ERROR | wx.OK)
            no_exception = False
        
        if no_exception:
            err_lines = [] #uncertainty bars

            data = []
            for x_value, y_value in datatable.as_rows(): #create uncertainty bars
                #value
                data_point = [x_value.value, y_value.value]
                data.append(data_point)

                #error bars
                #x unc
                err_lines.append(wx.lib.plot.PolyLine([[x_value.value - x_value.absolute_uncertainty, y_value.value], [x_value.value + x_value.absolute_uncertainty, y_value.value]], colour = 'black', width = 1))

                #y unc
                err_lines.append(wx.lib.plot.PolyLine([[x_value.value, y_value.value - y_value.absolute_uncertainty], [x_value.value, y_value.value + y_value.absolute_uncertainty]], colour = 'black', width = 1))
            
            lines.append(wx.lib.plot.PolyMarker(data, colour = 'black', width = 1, marker = 'cross', size = 1, legend = 'Data points')) #all data points

            if len(datatable.as_rows()) > 0 and show_regression: #calculate regression lines if there is any data
                fit_lines = sciplot.graphing.FitLines(datatable) #calculate fit lines
                fit_lines.calculate_all()

                #get ranges to plot over
                max_x = datatable.as_columns()[0][0].value
                min_x = datatable.as_columns()[0][0].value
                for value in datatable.as_columns()[0]:
                    if value.value + value.absolute_uncertainty > max_x:
                        max_x = value.value + value.absolute_uncertainty

                    if value.value - value.absolute_uncertainty < min_x:
                        min_x = value.value - value.absolute_uncertainty

                fit_lines_data = [(fit_lines.fit_best_gradient, fit_lines.fit_best_intercept, "green")]

                if None not in [fit_lines.fit_worst_max_gradient, fit_lines.fit_worst_max_intercept]: #there is a worst fit, so display it
                    fit_lines_data.append((fit_lines.fit_worst_max_gradient, fit_lines.fit_worst_max_intercept, "red"))
                
                if None not in [fit_lines.fit_worst_min_gradient, fit_lines.fit_worst_min_intercept]: #there is a worst fit, so display it
                    fit_lines_data.append((fit_lines.fit_worst_min_gradient, fit_lines.fit_worst_min_intercept, "red"))

                for gradient, intercept, colour in fit_lines_data:
                    if gradient is not None and intercept is not None: #construct lines and uncertainty bars
                        best_fit_points = [[min_x, intercept + (min_x * gradient)],
                                        [max_x, intercept + (max_x * gradient)]]

                        lines.append(wx.lib.plot.PolyLine(best_fit_points, colour = colour, width = 1))

            #put error bar lines last
            for line in err_lines:
                lines.append(line)

            return lines, x_value, y_value
        
        else:
            return None, None, None