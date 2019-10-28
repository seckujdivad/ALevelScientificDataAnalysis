import wx

import forms


class RootFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, title = "Data Analyser")

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self._btn_test = wx.Button(self, wx.ID_ANY, "Test button")
        self._gbs_main.Add(self._btn_test, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)

        self._frame_data = forms.DataFrame(self)
        self._gbs_main.Add(self._frame_data, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)
        self._frame_data.Show(True)

        for i in range(1):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(2):
            self._gbs_main.AddGrowableRow(j)

        self.subframes = {}

        self.SetSizer(self._gbs_main)
        self.Layout()

        self.Centre(wx.BOTH)


class App:
    def __init__(self):
        self.wx_app = wx.App()

        self.frame_root = RootFrame(None)
        self.frame_root.Show(True)

        self.wx_app.MainLoop()


if __name__ == '__main__':
    App()