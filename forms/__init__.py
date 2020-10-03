import wx

import typing

import sciplot.database
import sciplot.datafile


class SubFrame(wx.Panel):
    """
    Base class for the frames in the UI that are accessed through the bar at the top of the window

    Provides a few utility methods and attributes, as well as specifying default values for all of the attributes and methods that need to exist, but might not need implementing by each frame
    """
    def __init__(self, parent: wx.Simplebook, root_frame):
        super().__init__(parent, wx.ID_ANY)

        self.root_frame = root_frame
        self.parent: wx.Simplebook = parent

        self.identifier = 'null' #identifier used internally to differentiate between frames
        self.styling_name = '<blank>' #name of the frame to be displayed to the user when they hover over it
        self.styling_icon = wx.Bitmap('resources/toolbar/blank.bmp') #icon to be displayed to the user in the bar at the top of the window
        self.toolbar_index = -1 #position of the window in the bar at the top of the window, set by the root frame

        self.subframe_share: typing.Dict[str, typing.Any] = self.root_frame.subframe_share #dictionary containing data to be shared between frames

        self._datafile: sciplot.datafile.DataFile = self._datafile #property that gives the frame methods easy access to the database

        #A repeated piece of code from classes inheriting from this one is the sizer being created
        #The sizer is a grid that defines how GUI elements are arranged and resized in the window
        #There are multiple different types and configurations depending on the type of GUI you want
        #to create, so I have left constructing one to the inheriting classes
    
    def get_menu_items(self) -> typing.List[typing.Tuple[str, typing.List[typing.Tuple[str, typing.Callable[[], None]]]]]: #this method is to be queried by the root frame when it is creating the menu bar at the top of the screen and needs options to put in it
        """
        Get custom menu items to display on menubar

        Returns:
            list of
                tuple of
                    str: name of menu column
                    list of
                        tuple of
                            str: title of menu item
                            func: method to call when menu item is clicked
        """
        return []
    
    #hooks - these are called by the root frame when an event happens
    def hook_file_opened(self):
        """
        Method called by root frame when a file is opened. Should be overwritten by inheriting class
        """
    
    def hook_frame_selected(self):
        """
        Method called by root frame when this frame is selected. Should be overwritten by inheriting class
        """
    
    def hook_frame_unselected(self):
        """
        Method called by root frame when this frame is unselected. Should be overwritten by inheriting class
        """
    
    #ui binds
    #These methods all start _bind_ and are only meant to be bound to UI events. They aren't meant to form any part of a public API
    #They are added by the inheriting class
    
    #properties
    @property
    def _datafile(self) -> sciplot.datafile.DataFile: #_datafile getter
        if 'file' in self.subframe_share:
            return self.subframe_share['file']
        else:
            return None
    
    @_datafile.setter
    def _datafile(self, value): #_datafile setter
        self.subframe_share['file'] = value


#python seems to prefer the imports to be after SubFrame, or SubFrame won't be defined in the imports
import forms.frame_data
import forms.frame_variables
import forms.frame_graph
import forms.frame_datapoints
import forms.frame_constants
import forms.frame_import


manifest: typing.List[SubFrame] = [
    forms.frame_data.DataFrame,
    forms.frame_variables.VariablesFrame,
    forms.frame_datapoints.DataPointsFrame,
    forms.frame_graph.GraphFrame,
    forms.frame_constants.ConstantsFrame,
    forms.frame_import.ImportFrame
    ] #list of frames to be included in the bar at the top of the window