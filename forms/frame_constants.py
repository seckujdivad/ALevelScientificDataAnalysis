import wx

import forms
import sciplot.database


class ConstantsFrame(forms.SubFrame):
    """
    UI frame for editing constants and their units
    """
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'constants'
        self.styling_name = 'Constants'
        self.styling_icon = wx.Bitmap('resources/toolbar/constants.bmp')

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self._constant_ids = [] #primary keys of the loaded constants
        self._constant_symbols = [] #symbols of the loaded constants aligned with _constant_ids
        self._unit_ids = [] #unit composite primary keys of the loaded constants aligned with _constant_ids
        self._base_unit_data = [] #tuples containing the primary keys and symbols of the SI base units
        self._unit_table = {} #stores units for the selected constant in the format key: unit symbol, value: unit power
        self._old_constant_selection = None #index of previous constant selection in _constant_ids

        #create elements
        self._lb_constants = wx.ListBox(self, wx.ID_ANY)
        self._lb_constants.Bind(wx.EVT_LISTBOX, self._bind_lb_constants_selected)
        self._gbs_main.Add(self._lb_constants, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._spn_value = wx.SpinCtrlDouble(self, wx.ID_ANY, min = -9999, max = 9999)
        self._spn_value.SetDigits(10) #maximum digits in the spinbox. I would set it higher, but it is capped at 20 and at 20 digits, double imprecision is a factor
        self._spn_value.Bind(wx.EVT_SPINCTRLDOUBLE, self._bind_spn_value_changed)
        self._spn_value.Bind(wx.EVT_TEXT, self._bind_spn_value_changed)
        self._gbs_main.Add(self._spn_value, wx.GBPosition(1, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._entry_name = wx.TextCtrl(self, wx.ID_ANY)
        self._entry_name.Bind(wx.EVT_TEXT, self._bind_entry_name_changed)
        self._gbs_main.Add(self._entry_name, wx.GBPosition(2, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._btn_add_new = wx.Button(self, wx.ID_ANY, "Add New")
        self._btn_add_new.Bind(wx.EVT_BUTTON, self._bind_btn_add_new_clicked)
        self._gbs_main.Add(self._btn_add_new, wx.GBPosition(3, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove = wx.Button(self, wx.ID_ANY, "Remove")
        self._btn_remove.Bind(wx.EVT_BUTTON, self._bind_btn_remove_clicked)
        self._gbs_main.Add(self._btn_remove, wx.GBPosition(3, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lb_units = wx.ListBox(self, wx.ID_ANY)
        self._lb_units.Bind(wx.EVT_LISTBOX, self._bind_lb_units_selected)
        self._gbs_main.Add(self._lb_units, wx.GBPosition(0, 2), wx.GBSpan(3, 1), wx.ALL | wx.EXPAND)

        self._spn_power = wx.SpinCtrlDouble(self, wx.ID_ANY, min = -9999, max = 9999)
        self._spn_power.SetDigits(10)
        self._spn_power.Bind(wx.EVT_SPINCTRLDOUBLE, self._bind_spn_power_changed)
        self._spn_power.Bind(wx.EVT_TEXT, self._bind_spn_power_changed)
        self._gbs_main.Add(self._spn_power, wx.GBPosition(3, 2), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [0, 1, 2]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [0]:
            self._gbs_main.AddGrowableRow(j)
        
        #finalise layout
        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh_constants_list()
        self.refresh_units_list()
    
    def hook_frame_selected(self):
        self.refresh_constants_list()
    
    def hook_frame_unselected(self):
        self.store_spin_value()

    #ui binds
    def _bind_lb_constants_selected(self, event):
        selection = self._lb_constants.GetSelection()
        if selection != -1:
            #store old value
            self.store_spin_value(old = True)
            self.store_power_value(old = True)

            #get new value
            value, symbol = self._datafile.query(sciplot.database.Query("SELECT `Value`, Symbol FROM Constant WHERE ConstantID = (?);", [self._constant_ids[selection]], 2))[0]
            self._spn_value.SetValue(value)
            self._entry_name.SetValue(symbol)

            #load units
            unit_powers_raw = self._datafile.query(sciplot.database.Query('SELECT Unit.Symbol, UnitCompositeDetails.Power FROM Unit INNER JOIN UnitCompositeDetails ON Unit.UnitID = UnitCompositeDetails.UnitID WHERE UnitCompositeDetails.UnitCompositeID = (?);', [self._unit_ids[selection]], 1))[0]

            self._unit_table = {key: value for key, value in unit_powers_raw} #change from tuple pairs to dictionary
            self.refresh_unit_selection()

            self._old_constant_selection = selection

        event.Skip()
    
    def _bind_spn_value_changed(self, event):
        self.store_spin_value()
        event.Skip()

    def _bind_btn_add_new_clicked(self, event):
        #write data from previously selected constant to the database
        self.store_spin_value(old = True)
        self.store_power_value(old = True)

        unit_id = self._datafile.create_unit(None, [(1, 1)])
        constant_id = self._datafile.query([sciplot.database.Query("INSERT INTO Constant (Symbol, UnitCompositeID, Value) VALUES ((?), (?), 0)", [self._entry_name.GetValue(), unit_id], 0),
                                            sciplot.database.Query("SELECT last_insert_rowid();", [], 2)])[0][0] #add a new constant to the database
        
        self._datafile.update_units("Constant", constant_id, None, []) #give the new constant blank units

        #put default values into ui
        self._spn_value.SetValue(0)
        self._spn_power.SetValue(0)

        #update constant list to show new constant
        self.refresh_constants_list()
        self._unit_table = {}
        self.refresh_unit_selection()

        event.Skip()

    def _bind_btn_remove_clicked(self, event):
        selection = self._lb_constants.GetSelection()
        if selection != -1:
            self._datafile.query(sciplot.database.Query("DELETE FROM Constant WHERE ConstantID = (?);", [self._constant_ids[selection]], 0))
            self._datafile.prune_unused_composite_units() #remove units of the deleted constant from the database
            self.refresh_constants_list()

        event.Skip()
    
    def _bind_lb_units_selected(self, event):
        self.refresh_unit_selection()
        event.Skip()

    def _bind_spn_power_changed(self, event):
        self.store_power_value()
        event.Skip()
    
    def _bind_entry_name_changed(self, event):
        selection = self._lb_constants.GetSelection()
        if selection != -1:
            self._datafile.query(sciplot.database.Query("UPDATE Constant SET Symbol = (?) WHERE ConstantID = (?);", [self._entry_name.GetValue(), self._constant_ids[selection]], 0))
            self.refresh_constants_list()

        event.Skip()

    #frame methods
    def refresh_constants_list(self):
        """
        Updates the list of constants from the database
        """
        selection = self._lb_constants.GetSelection()

        self._lb_constants.Clear()
        self._constant_ids.clear()
        self._unit_ids.clear()
        self._constant_symbols.clear()
        for constant_id, constant_symbol, constant_unit_id in self._datafile.query(sciplot.database.Query("SELECT ConstantID, Symbol, UnitCompositeID FROM Constant;", [], 1))[0]: #unpack values into memory
            self._lb_constants.Append(constant_symbol)
            self._constant_symbols.append(constant_symbol)
            self._constant_ids.append(constant_id)
            self._unit_ids.append(constant_unit_id)

        if selection != -1:
            self._lb_constants.SetSelection(selection)
    
    def store_spin_value(self, old = False):
        """
        Stores the value of the selected constant in the database
        """
        if old == True:
            if self._old_constant_selection is None:
                selection = -1
            else:
                selection = self._old_constant_selection
        else:
            selection = self._lb_constants.GetSelection()

        if selection != -1: #there is a value selected, so store it in the database
            value = self._spn_value.GetValue()
            self._datafile.query(sciplot.database.Query("UPDATE Constant SET `Value` = (?)  WHERE ConstantID = (?);", [value, self._constant_ids[selection]], 0))
    
    def refresh_units_list(self):
        """
        Updates the list of base SI units from the database
        """
        selection = self._lb_units.GetSelection()

        self._base_unit_data.clear()
        self._lb_units.Clear()

        for unit_id, unit_symbol in self._datafile.query(sciplot.database.Query("SELECT UnitID, Symbol FROM Unit;", [], 1))[0]: #get units from database
            self._base_unit_data.append((unit_id, unit_symbol))
            self._lb_units.Append(unit_symbol)

        if selection != -1:
            self._lb_units.SetSelection(selection)
    
    def refresh_unit_selection(self):
        """
        Updates the power in the spin box of the selected base SI unit for the constant
        """
        selection = self._lb_units.GetSelection()
        if selection != -1:
            unit_id, unit_symbol = self._base_unit_data[selection]

            if unit_symbol in self._unit_table:
                self._spn_power.SetValue(self._unit_table[unit_symbol])
            else:
                self._spn_power.SetValue(0)

        else:
            self._spn_power.SetValue(0)
    
    def store_power_value(self, old = False):
        """
        Stores the new power in the spin box for the selected base SI unit in the database for the selected constant
        """
        if old == True:
            if self._old_constant_selection is None:
                constant_selection = -1
            else:
                constant_selection = self._old_constant_selection
        else:
            constant_selection = self._lb_constants.GetSelection()

        unit_selection = self._lb_units.GetSelection()
        
        if constant_selection != -1 and unit_selection != -1: #a unit and a constant is selected, so the power needs storing
            value = self._spn_power.GetValue()
            unit_id, unit_symbol = self._base_unit_data[unit_selection]
            self._unit_table[unit_symbol] = value

            constant_id = self._constant_ids[constant_selection]
            unit_table = [(self._datafile.query(sciplot.database.Query("SELECT UnitID FROM Unit WHERE Symbol = (?);", [unit_symbol], 2))[0][0], self._unit_table[unit_symbol]) for unit_symbol in self._unit_table]

            self._datafile.update_units("Constant", constant_id, None, unit_table)

            self.refresh_constants_list()