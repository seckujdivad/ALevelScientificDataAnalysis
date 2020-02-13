import wx

import forms
import sciplot.database


class ConstantsFrame(forms.SubFrame):
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

        self._constant_ids = []
        self._old_constant_selection = None

        #create elements
        self._lb_constants = wx.ListBox(self, wx.ID_ANY)
        self._lb_constants.Bind(wx.EVT_LISTBOX, self._bind_lb_constants_selected)
        self._gbs_main.Add(self._lb_constants, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._spn_value = wx.SpinCtrlDouble(self, wx.ID_ANY)
        self._spn_value.SetDigits(10) #maximum digits in the spinbox. I would set it higher, but it is capped at 20 and at 20 digits, double imprecision is a factor
        self._spn_value.Bind(wx.EVT_SPINCTRLDOUBLE, self._bind_spn_value_changed)
        self._spn_value.Bind(wx.EVT_TEXT, self._bind_spn_value_changed)
        self._gbs_main.Add(self._spn_value, wx.GBPosition(1, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._btn_add_new = wx.Button(self, wx.ID_ANY, "Add New")
        self._btn_add_new.Bind(wx.EVT_BUTTON, self._bind_btn_add_new_clicked)
        self._gbs_main.Add(self._btn_add_new, wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove = wx.Button(self, wx.ID_ANY, "Remove")
        self._btn_remove.Bind(wx.EVT_BUTTON, self._bind_btn_remove_clicked)
        self._gbs_main.Add(self._btn_remove, wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._lb_units = wx.ListBox(self, wx.ID_ANY)
        self._gbs_main.Add(self._lb_units, wx.GBPosition(0, 2), wx.GBSpan(2, 1), wx.ALL | wx.EXPAND)

        self._spn_power = wx.SpinCtrlDouble(self, wx.ID_ANY)
        self._spn_power.SetDigits(10)
        self._gbs_main.Add(self._spn_power, wx.GBPosition(2, 2), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

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
    
    def hook_frame_selected(self):
        self.refresh_constants_list()
    
    def hook_frame_unselected(self):
        self.store_spin_value()

    #ui binds
    def _bind_lb_constants_selected(self, event):
        selection = self._lb_constants.GetSelection()
        if selection != -1:
            self.store_spin_value(old = True)

            value = self._datafile.query(sciplot.database.Query("SELECT `Value` FROM Constant WHERE ConstantID = (?);", [self._constant_ids[selection]], 2))[0][0]
            self._spn_value.SetValue(value)

            self._old_constant_selection = selection

        event.Skip()
    
    def _bind_spn_value_changed(self, event):
        self.store_spin_value()
        event.Skip()

    def _bind_btn_add_new_clicked(self, event):
        event.Skip()

    def _bind_btn_remove_clicked(self, event):
        event.Skip()

    #frame methods
    def refresh_constants_list(self):
        selection = self._lb_constants.GetSelection()

        self._lb_constants.Clear()
        self._constant_ids.clear()
        for constant_id, constant_symbol in self._datafile.query(sciplot.database.Query("SELECT ConstantID, Symbol FROM Constant;", [], 1))[0]:
            self._lb_constants.Append(constant_symbol)
            self._constant_ids.append(constant_id)

        if selection != -1:
            self._lb_constants.SetSelection(selection)
    
    def store_spin_value(self, old = False):
        if old == True:
            if self._old_constant_selection is None:
                selection = -1
            else:
                selection = self._old_constant_selection
        else:
            selection = self._lb_constants.GetSelection()

        if selection != -1:
            value = self._spn_value.GetValue()
            self._datafile.query(sciplot.database.Query("UPDATE Constant SET `Value` = (?)  WHERE ConstantID = (?);", [value, self._constant_ids[selection]], 0))