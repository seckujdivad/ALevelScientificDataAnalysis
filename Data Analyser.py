import wx
import wx.lib.agw.ribbon as ribbon

import forms


class RootFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, title = "Data Analyser")

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        #make sizer (organises the elements in the frame)
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #make ribbon
        self._rbn_main = ribbon.RibbonBar(self, wx.ID_ANY)

        ##ribbon home
        self._rbn_pg_home = ribbon.RibbonPage(self._rbn_main, wx.ID_ANY, "Home", wx.NullBitmap)
        self._rbn_pnl_home = ribbon.RibbonPanel(self._rbn_pg_home, wx.ID_ANY, "Toolbar", wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, agwStyle = ribbon.RIBBON_PANEL_NO_AUTO_MINIMISE)

        ###load/save toolbar
        self._rbn_pnl_home_file = ribbon.RibbonToolBar(self._rbn_pnl_home, wx.ID_ANY)
        self._rbn_pnl_home_file.AddTool(wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_OTHER, wx.Size(16, 15)))
        self._rbn_pnl_home_file.AddTool(wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, wx.Size(16, 15)))
        self._rbn_pnl_home_file.AddSeparator()
        self._rbn_pnl_home_file.AddTool(wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, wx.Size(16, 15)))
        self._rbn_pnl_home_file.SetRows(1, 3)

        self._rbn_main.Realize()
        self._gbs_main.Add(self._rbn_main, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND, 0)

        self._btn_test = wx.Button(self, wx.ID_ANY, "Test button")
        self._gbs_main.Add(self._btn_test, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)

        self._frame_data = forms.DataFrame(self)
        self._gbs_main.Add(self._frame_data, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)
        self._frame_data.Show(True)

        for i in range(2):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(1, 2, 1):
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