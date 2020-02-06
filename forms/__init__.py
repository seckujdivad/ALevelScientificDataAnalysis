import wx

import typing

import sciplot.database


class SubFrame(wx.Panel):
    def __init__(self, parent, root_frame):
        super().__init__(parent, wx.ID_ANY)

        self.root_frame = root_frame
        self.parent = parent

        self.identifier = 'null'
        self.styling_name = '<blank>'
        self.styling_icon = wx.Bitmap('resources/toolbar/blank.bmp')
        self.toolbar_index = -1

        self.subframe_share = self.root_frame.subframe_share

        self._datafile: sciplot.database.DataFile = self._datafile
    
    def get_menu_items(self):
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
    
    #hooks
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
    
    #properties
    @property
    def _datafile(self):
        if 'file' in self.subframe_share:
            return self.subframe_share['file']
        else:
            return None
    
    @_datafile.setter
    def _datafile(self, value):
        self.subframe_share['file'] = value


#python seems to prefer the imports to be after SubFrame, or SubFrame won't be defined in the imports
import forms.frame_data
import forms.frame_variables
import forms.frame_graph
import forms.frame_datapoints


manifest: typing.List[SubFrame] = [forms.frame_data.DataFrame, forms.frame_variables.VariablesFrame, forms.frame_datapoints.DataPointsFrame, forms.frame_graph.GraphFrame]