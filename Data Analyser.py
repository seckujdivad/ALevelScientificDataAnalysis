import wx

import forms


class RootFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, title = "Data Analyser")

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self._pnl_frames = wx.Panel(self, wx.ID_ANY)

        self.subframes = {}


class App:
    def __init__(self):
        self.wx_app = wx.App()

        self.frame_root = RootFrame(None)
        self.frame_root.Show(True)

        self.wx_app.MainLoop()


if __name__ == '__main__':
    App()