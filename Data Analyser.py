import wx
import wx.lib.agw.ribbon as ribbon
import typing
import functools

import forms


class RootFrame(wx.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, wx.ID_ANY, title = "Data Analyser")

        self.app = app

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.SetSize(800, 600)

        #make sizer (organises the elements in the frame)
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #set growable regions
        for i in range(0, 1, 1):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(1, 2, 1):
            self._gbs_main.AddGrowableRow(j)

        #make toolbar
        self._tlbr_panelswitch = wx.ToolBar(self, wx.ID_ANY)
        self._tlbr_panelswitch_tools = {}

        #make panel embedding UI
        self._pnl_sub = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize)
        self._gbs_main.Add(self._pnl_sub, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.EXPAND, 0)        

        self._subframes: typing.Dict[str, forms.SubFrame] = {} #type hints - only for editor
        self._current_frame = None
        for FrameType in forms.manifest:
            new_frame = FrameType(self._pnl_sub, self)
            self._subframes[new_frame.identifier] = new_frame
            self._tlbr_panelswitch_tools[new_frame.identifier] = self._tlbr_panelswitch.AddTool(wx.ID_ANY, new_frame.styling_name, new_frame.styling_icon)
            self.Bind(wx.EVT_TOOL, functools.partial(self.toolbar_form_clicked, new_frame.identifier), self._tlbr_panelswitch_tools[new_frame.identifier])

            if isinstance(new_frame, forms.manifest[0]):
                self.set_form(new_frame.identifier)

        #controls have been added, make toolbar static
        self._tlbr_panelswitch.Realize()
        self._gbs_main.Add(self._tlbr_panelswitch, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)

        #make status bar
        self._sb_main = self.CreateStatusBar(1, wx.STB_SIZEGRIP, wx.ID_ANY)

        #configure layout
        self.SetSizer(self._gbs_main)
        self.Layout()

        self.Centre(wx.BOTH)
    
    def set_form(self, form):
        if self._current_frame != form:
            if self._current_frame is not None:
                self._subframes[self._current_frame].Hide()
            
                self._subframes[form].Show()
                self._current_frame = form
    
    def toolbar_form_clicked(self, name, event):
        self.set_form(name)
        event.Skip()


class App(wx.App):
    def __init__(self):
        super().__init__()

        self.frame_root = RootFrame(None, self)
        self.frame_root.Show(True)

        self.MainLoop()


if __name__ == '__main__':
    App()