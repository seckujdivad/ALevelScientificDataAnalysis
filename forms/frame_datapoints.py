import wx
import wx.dataview

import forms

import sciplot.database


class DataPointsFrame(forms.SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'datapoints'
        self.styling_name = 'Data Points'
        self.styling_icon = wx.Bitmap('resources/toolbar/formulae.bmp')

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #create elements
        self._lb_datasets = wx.ListBox(self, wx.ID_ANY)
        self._gbs_main.Add(self._lb_datasets, wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._dvl_datapoints = wx.dataview.DataViewListCtrl(self, wx.ID_ANY)
        self._dvc_col = self._dvl_datapoints.AppendTextColumn("Value")

        self._gbs_main.Add(self._dvl_datapoints, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [0, 1]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [0]:
            self._gbs_main.AddGrowableRow(j)
        
        #finalise layout
        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh_dataset_list()
    
    def hook_frame_selected(self):
        self.refresh_dataset_list()
        self.resize_datapoint_columns()
    
    #ui binds

    #frame methods
    def refresh_dataset_list(self):
        pass

    def resize_datapoint_columns(self):
        width = self._dvl_datapoints.GetSize()[0]
        self._dvc_col.SetWidth(width)