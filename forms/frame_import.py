import wx
import wx.dataview
import csv

import forms


class ImportFrame(forms.SubFrame):
    """
    UI frame for importing data from external formats
    """
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'import'
        self.styling_name = 'Import'
        self.styling_icon = wx.Bitmap('resources/toolbar/constants.bmp') #TODO: replace when a proper icon is made

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #create elements
        self._btn_choose_file = wx.Button(self, wx.ID_ANY, "Import CSV")
        self._gbs_main.Add(self._btn_choose_file, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._dvl_data: wx.dataview.DataViewListCtrl = None #DataViewListCtrls can't have their columns dynamically changed, so this is deferred to a method (more about this in forms.frame_data.py)
        self._recreate_dvl_data()

        #set sizer weights
        for i in [0]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [1]:
            self._gbs_main.AddGrowableRow(j)
        
        #finalise layout
        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)
    
    #root frame hooks
    def hook_file_opened(self):
        pass
    
    def hook_frame_selected(self):
        pass
    
    def hook_frame_unselected(self):
        pass

    #ui binds
    def _bind_btn_choose_file_clicked(self, event):
        event.Skip()

    #frame methods
    def _recreate_dvl_data(self):
        """
        DataViewListCtrls aren't fully dynamic, so I recreate them every time here
        See the same method in forms/frame_data.py for the same solution
        """
        if self._dvl_data is not None:
            self._dvl_data.Destroy()
        
        self._dvl_data = wx.dataview.DataViewListCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._dvl_data, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)
        self.Layout()