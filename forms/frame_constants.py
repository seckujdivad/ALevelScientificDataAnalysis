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

        #create elements
        self._lb_constants = wx.ListBox(self, wx.ID_ANY)
        self._lb_constants.Bind(wx.EVT_LISTBOX, self._bind_lb_constants_selected)
        self._gbs_main.Add(self._lb_constants, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._spn_value = wx.SpinCtrlDouble(self, wx.ID_ANY)
        self._spn_value.SetDigits(10) #maximum digits in the spinbox. I would set it higher, but it is capped at 20 and at 20 digits, double imprecision is a factor
        self._lb_constants.Bind(wx.EVT_SPINCTRLDOUBLE, self._bind_spn_value_changed)
        self._gbs_main.Add(self._spn_value, wx.GBPosition(1, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._btn_add_new = wx.Button(self, wx.ID_ANY, "Add New")
        self._lb_constants.Bind(wx.EVT_BUTTON, self._bind_btn_add_new_clicked)
        self._gbs_main.Add(self._btn_add_new, wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove = wx.Button(self, wx.ID_ANY, "Remove")
        self._lb_constants.Bind(wx.EVT_BUTTON, self._bind_btn_remove_clicked)
        self._gbs_main.Add(self._btn_remove, wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [0, 1]:
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

    #ui binds
    def _bind_lb_constants_selected(self, event):
        selection = self._lb_constants.GetSelection()
        if selection != -1:
            value = self._datafile.query(sciplot.database.Query("SELECT `Value` FROM Constant WHERE ConstantID = (?);", [self._constant_ids[selection]], 2))[0][0]
            self._spn_value.SetValue(value)

        event.Skip()
    
    def _bind_spn_value_changed(self, event):
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