import wx
import wx.lib.agw.ribbon as ribbon
import typing
import functools
import ctypes

import forms


class RootFrame(wx.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, wx.ID_ANY, title = "Data Analyser")

        self.app = app

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.SetSize(800, 600)
        self.SetMinSize(wx.Size(500, 400))

        #set icon
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("resources/icon.ico", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        #make sizer (organises the elements in the frame)
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #set growable regions
        for i in range(0, 1, 1):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(1, 2, 1):
            self._gbs_main.AddGrowableRow(j)

        #make status bar
        self._sb_main = self.CreateStatusBar(1, wx.STB_SIZEGRIP, wx.ID_ANY)
        self._sb_main.PushStatusText("")

        #make toolbar
        self._tlbr_panelswitch = wx.ToolBar(self, wx.ID_ANY)
        self._tlbr_panelswitch_tools: typing.Dict[str, wx.ToolBarToolBase] = {}

        #make panel embedding UI
        self._bk_sub = wx.Simplebook(self, wx.ID_ANY)
        self._gbs_main.Add(self._bk_sub, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.EXPAND, 0)

        self._subframes: typing.Dict[str, forms.SubFrame] = {} #type hints - only for editor
        self._current_frame = None
        i = 0
        for FrameType in forms.manifest:
            new_frame = FrameType(self._bk_sub, self)
            self._subframes[new_frame.identifier] = new_frame
            self._tlbr_panelswitch_tools[new_frame.identifier] = self._tlbr_panelswitch.AddTool(wx.ID_ANY, new_frame.styling_name, new_frame.styling_icon)
            self._tlbr_panelswitch_tools[new_frame.identifier].SetLongHelp(new_frame.styling_name)

            self.Bind(wx.EVT_TOOL, functools.partial(self.toolbar_form_clicked, new_frame.identifier), self._tlbr_panelswitch_tools[new_frame.identifier])
            self._bk_sub.ShowNewPage(new_frame)

            new_frame.toolbar_index = i
            i += 1

            if isinstance(new_frame, forms.manifest[0]):
                self.set_form(new_frame.identifier)

        #controls have been added, make toolbar static
        self._tlbr_panelswitch.Realize()
        self._gbs_main.Add(self._tlbr_panelswitch, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)

        #configure layout
        self.SetSizer(self._gbs_main)
        self.Layout()

        self.Centre(wx.BOTH)

        self.set_form("data", True)
    
    def set_form(self, form, override = False):
        if override or self._current_frame != form:
            if self._subframes[form].toolbar_index == -1:
                raise Exception("This form hasn't been connected to a SimpleBook")

            self._bk_sub.SetSelection(self._subframes[form].toolbar_index)
            self._sb_main.PopStatusText()
            self._sb_main.PushStatusText(self._subframes[form].styling_name)
            self._current_frame = form
    
    def toolbar_form_clicked(self, name, event):
        self.set_form(name)
        event.Skip()


class App(wx.App):
    def __init__(self):
        super().__init__()

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("davidjuckes.sciplot")

        self.frame_root = RootFrame(None, self)
        self.frame_root.Show(True)

        self.MainLoop()


if __name__ == '__main__':
    App()