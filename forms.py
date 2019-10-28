import wx


class DataFrame(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self._btn_test = wx.Button(self, wx.ID_ANY, "Test button 2 - data")
        self._gbs_main.Add(self._btn_test, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)

        for i in range(1):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(1):
            self._gbs_main.AddGrowableRow(j)

        self.SetSizer(self._gbs_main)
        self.Layout()

        self.Centre(wx.BOTH)