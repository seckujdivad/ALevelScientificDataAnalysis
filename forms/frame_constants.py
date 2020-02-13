import wx

import forms


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

        #create elements
        self._lb_constants = wx.ListBox(self, wx.ID_ANY)
        self._lb_constants.Bind(wx.EVT_LISTBOX, self._bind_lb_constants_selected)
        self._gbs_main.Add(self._lb_constants, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._spn_value = wx.SpinCtrlDouble(self, wx.ID_ANY)
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

    #ui binds
    def _bind_lb_constants_selected(self, event):
        event.Skip()
    
    def _bind_spn_value_changed(self, event):
        event.Skip()

    def _bind_btn_add_new_clicked(self, event):
        event.Skip()

    def _bind_btn_remove_clicked(self, event):
        event.Skip()

    #frame methods