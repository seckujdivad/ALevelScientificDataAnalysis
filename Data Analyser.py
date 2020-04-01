import wx
import wx.lib.agw.ribbon as ribbon

import typing
import functools
import ctypes
import sys
import shutil
import os
import ntpath

import forms
import sciplot.database
import sciplot.datafile


class RootFrame(wx.Frame):
    def __init__(self, app):
        super().__init__(None, wx.ID_ANY, title = "Data Analyser")

        self.app = app

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.SetSize(800, 600)
        self.SetMinSize(wx.Size(500, 400))

        #a dictionary for sharing data between frames
        #in theory, it could be used for any data
        #however, it is only used for sharing the file object between the frames (so they don't have their own separate connections)
        self.subframe_share = {
            'file': None,
            'file is temp': True
        }

        #make temp datafile
        #sciplot.datafile.create_blank_datafile("user/temp.db")
        if os.path.isfile(os.path.join('user', 'temp.db')):
            os.remove(os.path.join('user', 'temp.db'))
        self.subframe_share['file'] = sciplot.datafile.DataFile("user/temp.db")
        self.subframe_share['file'].initialise_tables()

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

        #make menu bar
        self._mb_main = wx.MenuBar()
        self._mb_cats = {}
        self._mb_subitems = {}
        self._mb_cats_internalonly = {}
        for name in ['File', 'Help']: #add menu bar categories
            self._mb_cats[name] = wx.Menu()
            self._mb_main.Append(self._mb_cats[name], name)
            self._mb_subitems[name] = []
            self._mb_cats_internalonly[name] = True
        self.SetMenuBar(self._mb_main)

        #add internal menu bar items
        for cat, title, func in [('File', 'Open', self._choose_db), ('File', 'Save', self._commit_db), ('File', 'Save As (temporary files)', self._save_temp), ('Help', 'Quickstart', self._help_quickstart)]:
            menu_item = self._mb_cats[cat].Append(wx.ID_ANY, title)
            self.Bind(wx.EVT_MENU, func, menu_item)
            self._mb_subitems[cat].append(menu_item)

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
            new_frame.hook_file_opened()

            new_frame.toolbar_index = i

            #register menu items
            menu_items = new_frame.get_menu_items()
            for name, items in menu_items:
                for title, func in items:
                    if self._mb_cats_internalonly[name]:
                        self._mb_cats[name].AppendSeparator()
                        self._mb_cats_internalonly[name] = False

                    menu_item = self._mb_cats[name].Append(wx.ID_ANY, title)
                    self.Bind(wx.EVT_MENU, func, menu_item)
                    self._mb_subitems[name].append(menu_item)

            if isinstance(new_frame, forms.manifest[0]):
                self.set_form(new_frame.identifier)
            
            i += 1

        #controls have been added, make toolbar static
        self._tlbr_panelswitch.Realize()
        self._gbs_main.Add(self._tlbr_panelswitch, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND, 0)

        #configure layout
        self.SetSizer(self._gbs_main)
        self.Layout()

        self.Centre(wx.BOTH)

        self.set_form("data", True) #choose the data form when the program first opens
    
    def set_form(self, form, override = False): #choose a form (tab from the title bar at the top of the window)
        if override or self._current_frame != form:
            if self._subframes[form].toolbar_index == -1:
                raise Exception("This form hasn't been connected to a SimpleBook")

            if self._current_frame is not None:
                self._subframes[self._current_frame].hook_frame_unselected()

            self._bk_sub.SetSelection(self._subframes[form].toolbar_index)
            self._sb_main.PopStatusText()
            self._subframes[form].hook_frame_selected()
            self._sb_main.PushStatusText(self._subframes[form].styling_name + '  ')
            self._current_frame = form
    
    def toolbar_form_clicked(self, name, event):
        self.set_form(name)
        event.Skip()
    
    def _choose_db(self, event): #open a file
        if self.subframe_share['file'] is not None and not self.subframe_share['file is temp']: #save file (if the open file is not temporary)
            commit_changes = wx.MessageBox("Commit changes to open file?", "Action required", wx.ICON_QUESTION | wx.OK | wx.CANCEL)

            if commit_changes == wx.OK:
                self.subframe_share['file'].commit()
                self.subframe_share['file'].close()
                self.subframe_share['file'] = None

        else:
            commit_changes = wx.OK

        if commit_changes != wx.CANCEL:
            with wx.FileDialog(self, "Open DataFile", wildcard = "DataFile (*.db)|*.db", defaultDir = sys.path[0], style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    pass

                else:
                    if self.subframe_share['file is temp']:
                        if self.subframe_share['file'] is not None:
                            self.subframe_share['file'].close()
                        os.remove("user/temp.db")
                        self.subframe_share['file is temp'] = False

                    path = file_dialog.GetPath()
                    
                    self.subframe_share['file'] = sciplot.datafile.DataFile(path)
                    
                    if self.subframe_share['file'].tables_are_valid():
                        for frame in self._subframes:
                            self._subframes[frame].hook_file_opened()
                    
                        self._set_title_file(ntpath.basename(path))
                    
                    else:
                        wx.MessageBox("This database doesn't contain the correct tables", "Invalid file", wx.ICON_ERROR | wx.OK)                    

        event.Skip()
    
    def _commit_db(self, event):
        if self.subframe_share['file is temp']:
            self._save_temp(event)

        elif self.subframe_share['file'] is None:
            wx.MessageBox("Can't save open file when there is no file open", "No file open", wx.ICON_ERROR | wx.OK)
        
        else:
            self.subframe_share['file'].commit()
    
    def on_window_close(self):
        if self.subframe_share['file'] is not None:
            self.subframe_share['file'].commit()
            self.subframe_share['file'].close()
    
    def _save_temp(self, event): #if the file open is temporary, ask the user for a name and move it to the location
        if self.subframe_share['file is temp']:
            with wx.FileDialog(self, "Save DataFile", wildcard = "DataFile (*.db)|*.db", defaultDir = sys.path[0], style = wx.FD_SAVE) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    pass

                else:
                    path = file_dialog.GetPath()
                    self.subframe_share['file'].commit()
                    self.subframe_share['file'].close()

                    shutil.copyfile("user/temp.db", path)
                    os.remove("user/temp.db")

                    self.subframe_share['file'] = sciplot.datafile.DataFile(path)
                    self.subframe_share['file is temp'] = False
        
        else:
            wx.MessageBox("Currently open file is not temporary", "File not temporary", wx.ICON_ERROR | wx.OK)
    
    def _set_title_file(self, name): #set title of window to contain the file name
        self.SetTitle('Data Analyser: {}'.format(name))
    
    def _help_quickstart(self, event): #show short explanation string
        wx.MessageBox("""Wondering where to start?
Try opening an example in user/examples to get a sense for how data can be processed.
You can start using this program straight away, but make sure to save before closing.
You will then be asked for a save location. Also, click on the "Variables" help to
read about the variable system.""", "Quickstart guide", style = wx.ICON_NONE)
        event.Skip()


class App(wx.App):
    def __init__(self):
        super().__init__()

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("davidjuckes.sciplot")

        self.frame_root = RootFrame(self)
        self.frame_root.Show(True)

        self.MainLoop()

        self.frame_root.on_window_close()


if __name__ == '__main__':
    App()