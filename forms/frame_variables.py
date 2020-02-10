import wx
import wx.propgrid
import typing

import forms
import sciplot.database
import sciplot.functions


class VariablesFrame(forms.SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'variables'
        self.styling_name = 'Variables'
        self.styling_icon = wx.Bitmap('resources/toolbar/variables.bmp')

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        
        #create elements
        self._lb_variables = wx.ListBox(self, wx.ID_ANY)
        self._lb_variables.Bind(wx.EVT_LISTBOX, self._bind_lb_variables_new_selection, self._lb_variables)
        self._gbs_main.Add(self._lb_variables, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._variable_data = []
        self._variable_current = None

        self._bk_props = wx.Simplebook(self, wx.ID_ANY)

        self._prop_dataset = wx.propgrid.PropertyGrid(self._bk_props, wx.ID_ANY)
        self._prop_dataset.Bind(wx.propgrid.EVT_PG_CHANGED, self._bind_property_changed)
        self._prop_formula = wx.propgrid.PropertyGrid(self._bk_props, wx.ID_ANY)
        self._prop_formula.Bind(wx.propgrid.EVT_PG_CHANGED, self._bind_property_changed)

        self._prop_dataset.SetColumnCount(2)

        self._prop_formula.SetColumnCount(2)
        self._prop_formula.Append(wx.propgrid.StringProperty('Symbol', 'symbol', 'name'))
        self._prop_formula.Append(wx.propgrid.StringProperty('Formula', 'formula', '0'))

        self._bk_props.ShowNewPage(self._prop_dataset)
        self._bk_props.ShowNewPage(self._prop_formula)
        
        self._gbs_main.Add(self._bk_props, wx.GBPosition(0, 2), wx.GBSpan(3, 1), wx.ALL | wx.EXPAND)

        self._btn_new_dataset = wx.Button(self, wx.ID_ANY, "New Dataset")
        self._btn_new_dataset.Bind(wx.EVT_BUTTON, self._bind_btn_new_dataset_clicked)
        self._gbs_main.Add(self._btn_new_dataset, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_new_formula = wx.Button(self, wx.ID_ANY, "New Formula")
        self._btn_new_formula.Bind(wx.EVT_BUTTON, self._bind_btn_new_formula_clicked)
        self._gbs_main.Add(self._btn_new_formula, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_delete = wx.Button(self, wx.ID_ANY, "Delete Variable")
        self._btn_delete.Bind(wx.EVT_BUTTON, self._bind_btn_delete_clicked)
        self._gbs_main.Add(self._btn_delete, wx.GBPosition(2, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        #finalise layout
        for i in range(3):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(1):
            self._gbs_main.AddGrowableRow(j)

        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)
    
    #root frame hooks
    def hook_file_opened(self):
        self._prop_dataset.Freeze()
        self._prop_dataset.Clear()

        self._prop_dataset.Append(wx.propgrid.StringProperty('Symbol', 'symbol', 'name'))

        self._prop_dataset.Append(wx.propgrid.FloatProperty('Uncertainty', 'unc', 0))
        self._prop_dataset.Append(wx.propgrid.BoolProperty('Uncertainty is percentage?', 'uncisperc', False))
        
        units_prop = self._prop_dataset.Append(wx.propgrid.StringProperty('Units', 'units'))

        for unit_name in self._datafile.query(sciplot.database.Query('SELECT Symbol FROM Unit;', [], 1))[0]:
            self._prop_dataset.AppendIn(units_prop, wx.propgrid.FloatProperty(unit_name[0], unit_name[0], 0))
        
        self._prop_dataset.Thaw()

        self.refresh_variable_list()
        self._centre_dividers()
    
    def hook_frame_selected(self):
        self._centre_dividers()
    
    #ui binds
    def _bind_btn_new_formula_clicked(self, event):
        formula_id = self._datafile.create_formula("0")
        self._datafile.create_variable("<blank>", 1, formula_id)
        self.refresh_variable_list()
        event.Skip()
    
    def _bind_btn_new_dataset_clicked(self, event):
        unit_id = self._datafile.create_unit("<blank>", [])
        data_set_id = self._datafile.create_data_set(0, False, unit_id)
        self._datafile.create_variable("<blank>", 0, data_set_id)
        self.refresh_variable_list()
        event.Skip()
    
    def _bind_lb_variables_new_selection(self, event):
        self.symbol_selected()
        event.Skip()

    def _bind_btn_delete_clicked(self, event):
        current_variable = self._lb_variables.GetSelection()
        if current_variable != -1:
            if len(self._variable_data) - 1 > 0:
                self._lb_variables.SetSelection((current_variable - 1) % (len(self._variable_data) - 1))

            variable_id = self._variable_data[current_variable][3]
            self._datafile.remove_variable(variable_id)

            self.refresh_variable_list()

            if len(self._variable_data) - 1 > 0:
                self._variable_current = current_variable % len(self._variable_data)
                self._lb_variables.SetSelection(self._variable_current)
                self.symbol_selected()

        event.Skip()
    
    def _bind_property_changed(self, property_event):
        selection = self._lb_variables.GetSelection()
        if selection != -1 and property_event.GetPropertyName() == "symbol":
            prop = property_event.GetProperty()
            self._datafile.query(sciplot.database.Query("UPDATE Variable SET Symbol = (?) WHERE VariableID = (?);", [prop.GetValue(), self._variable_data[selection][3]], 0))

            self.refresh_variable_list()

    #frame methods
    def selected_formula(self, var_id, var_symbol):
        self._bk_props.SetSelection(1)

        #get data
        expr = self._datafile.query(sciplot.database.Query('SELECT Formula.Expression FROM Formula INNER JOIN Variable ON Variable.ID = Formula.FormulaID WHERE Variable.Type = 1 AND Formula.FormulaID = (?);', [var_id], 2))[0][0]
        
        #load, modify and replace property sheet
        data = self._prop_formula.GetPropertyValues(inc_attributes = False)
        data['symbol'] = var_symbol
        data['formula'] = expr
        self._prop_formula.SetPropertyValues(data, autofill = False)
        self._prop_formula.Refresh()
    
    def selected_dataset(self, var_id, var_symbol):
        self._bk_props.SetSelection(0)

        #get data
        uncertainty, uncisperc, unit_id = self._datafile.query(sciplot.database.Query('SELECT DataSet.Uncertainty, DataSet.UncIsPerc, DataSet.UnitCompositeID FROM DataSet INNER JOIN Variable ON Variable.ID = DataSet.DataSetID AND Variable.Type = 0 WHERE DataSet.DataSetID = (?);', [var_id], 2))[0]
        
        #load data from property sheet and modify
        data = self._prop_dataset.GetPropertyValues(inc_attributes = False)
        data['symbol'] = var_symbol
        data['unc'] = uncertainty
        data['uncisperc'] = bool(uncisperc)
        data['units'] = self._datafile.get_unit_by_id(unit_id)[0]

        unit_powers_raw = self._datafile.query(sciplot.database.Query('SELECT Unit.Symbol, UnitCompositeDetails.Power FROM Unit INNER JOIN UnitCompositeDetails ON Unit.UnitID = UnitCompositeDetails.UnitID WHERE UnitCompositeDetails.UnitCompositeID = (?);', [unit_id], 1))[0]

        unit_powers = {key: value for key, value in unit_powers_raw} #change from tuple pairs to dictionary

        for name in data:
            if name.startswith('units.'):
                if name[6:] in unit_powers:
                    data[name] = unit_powers[name[6:]]
                else:
                    data[name] = 0

        #write modified property sheet back into propetry widget
        self._prop_dataset.SetPropertyValues(data, autofill = False)
        self._prop_dataset.Refresh()
    
    def symbol_selected(self):
        #store previous modifications
        if self._variable_current is not None:
            old_variable = self._variable_data[self._variable_current]

            if old_variable[1] == 0:
                data = self._prop_dataset.GetPropertyValues(inc_attributes = False)

                self._datafile.query(sciplot.database.Query("UPDATE Variable SET Symbol = (?) WHERE ID = (?) AND Type = 0;", [data['symbol'], old_variable[2]], 0))
                self._datafile.query(sciplot.database.Query("UPDATE DataSet SET Uncertainty = (?), UncIsPerc = (?) WHERE DataSetID = (?);", [data['unc'], data['uncisperc'], old_variable[2]], 0))

                unit_composite_id = self._datafile.query(sciplot.database.Query("SELECT UnitCompositeID FROM DataSet WHERE DataSetID = (?);", [old_variable[2]], 2))[0][0]

                units_table = []
                for unit_string in data:
                    if unit_string.startswith('units.'):
                        if data[unit_string] != 0:
                            units_table.append((self._datafile.query(sciplot.database.Query("SELECT UnitID FROM Unit WHERE Symbol = (?);", [unit_string[6:]], 2))[0][0], float(data[unit_string])))

                units_changed = False
                if self._datafile.query(sciplot.database.Query("SELECT Symbol FROM UnitComposite WHERE UnitCompositeID = (?);", [unit_composite_id], 2))[0][0] != data['units']:
                    units_changed = True
                if set(self._datafile.get_unit_by_id(unit_composite_id)[1]) != set(units_table):
                    units_changed = True

                if units_changed: #merge/split/edit current composite units
                    references = [tup[0] for tup in self._datafile.query(sciplot.database.Query("SELECT DataSetID FROM DataSet WHERE UnitCompositeID = (?);", [unit_composite_id], 1))[0]]

                    if len(references) > 1:
                        new_composite_id = self._datafile.create_unit(data['units'], units_table)
                        self._datafile.query(sciplot.database.Query("UPDATE DataSet SET UnitCompositeID = (?) WHERE DataSetID = (?);", [new_composite_id, old_variable[2]], 0))

                    else:
                        shared_units = self._datafile.get_unit_id_by_table(units_table)

                        potential_merges = []
                        for unit_id in shared_units:
                            if self._datafile.get_unit_by_id(unit_id)[0] == data['units'] and unit_id != unit_composite_id:
                                potential_merges.append(unit_id)
                        
                        if len(potential_merges) == 0:
                            self._datafile.rename_unit(unit_composite_id, data['units'])
                            self._datafile.update_unit(unit_composite_id, units_table)
                        else:
                            self._datafile.query(sciplot.database.Query("UPDATE DataSet SET UnitCompositeID = (?) WHERE DataSetID = (?);", [potential_merges[0], old_variable[2]], 0))
                            self._datafile.query(sciplot.database.Query("DELETE FROM UnitComposite WHERE UnitCompositeID = (?);", [unit_composite_id], 0))
                            self._datafile.query(sciplot.database.Query("DELETE FROM UnitCompositeDetails WHERE UnitCompositeID = (?);", [unit_composite_id], 0))

            else:
                data = self._prop_formula.GetPropertyValues(inc_attributes = False)

                func_lib = {}
                for expression, symbol in self._datafile.query(sciplot.database.Query("SELECT Expression, Symbol FROM Formula INNER JOIN Variable ON Variable.ID = Formula.FormulaID AND Type = 1;", [], 1))[0]:
                    func_lib[symbol] = sciplot.functions.Function(expression)
                
                func_lib[data['symbol']] = sciplot.functions.Function(data['formula'])
                
                if sciplot.functions.check_circular_dependencies(data['symbol'], func_lib):
                    wx.MessageBox("Circular dependency in your formula\nCheck the expression to make sure it doesn't refer to itself\nChanges will not be saved", "Circular dependency", wx.ICON_ERROR | wx.OK)
                
                else:
                    self._datafile.query(sciplot.database.Query("UPDATE Variable SET Symbol = (?) WHERE ID = (?) AND Type = 1;", [data['symbol'], old_variable[2]], 0))
                    self._datafile.query(sciplot.database.Query("UPDATE Formula SET Expression = (?) WHERE FormulaID = (?);", [data['formula'], old_variable[2]], 0))
        
        self._variable_current = self._lb_variables.GetSelection()
        variable = self._variable_data[self._variable_current]

        if variable[1] == 0:
            self.selected_dataset(variable[2], variable[0])
        else:
            self.selected_formula(variable[2], variable[0])
        
        self.refresh_variable_list()
    
    def _centre_dividers(self): #centre splitter in property pages so that the labels can be read
        self._bk_props.SetSelection(1)
        self._prop_formula.CenterSplitter()
        self._bk_props.SetSelection(0)
        self._prop_dataset.CenterSplitter()
    
    def refresh_variable_list(self):
        current_variable = self._lb_variables.GetSelection()

        self._variable_data.clear()
        self._lb_variables.Clear()
        for data in self._datafile.query(sciplot.database.Query('SELECT Symbol, Type, ID, VariableID FROM Variable;', [], 1))[0]:
            self._lb_variables.Append(data[0])
            self._variable_data.append(data)
        
        self._lb_variables.SetSelection(min(current_variable, len(self._variable_data) - 1))