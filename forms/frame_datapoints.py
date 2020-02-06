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
        self.styling_icon = wx.Bitmap('resources/toolbar/dataset.bmp')

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #create elements
        self._data_sets = []
        self._data_points = []

        self._lb_datasets = wx.ListBox(self, wx.ID_ANY)
        self._lb_datasets.Bind(wx.EVT_LISTBOX, self._bind_lb_datasets_new_selection)
        self._gbs_main.Add(self._lb_datasets, wx.GBPosition(0, 2), wx.GBSpan(3, 1), wx.ALL | wx.EXPAND)

        self._btn_add_new = wx.Button(self, wx.ID_ANY, "Add New")
        self._gbs_main.Add(self._btn_add_new, wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove = wx.Button(self, wx.ID_ANY, "Remove")
        self._gbs_main.Add(self._btn_remove, wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._dvl_datapoints = wx.dataview.DataViewListCtrl(self, wx.ID_ANY)
        self._dvc_col = self._dvl_datapoints.AppendTextColumn("Value")
        self._gbs_main.Add(self._dvl_datapoints, wx.GBPosition(0, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        self._spn_value = wx.SpinCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._spn_value, wx.GBPosition(1, 0), wx.GBSpan(1, 2), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [0, 1, 2]:
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
    def _bind_lb_datasets_new_selection(self, event):
        self.refresh_data_points()
        event.Skip()

    #frame methods
    def refresh_dataset_list(self):
        self._data_sets = self._datafile.query(sciplot.database.Query("SELECT DataSetID, Symbol FROM DataSet INNER JOIN Variable ON ID = DataSetID AND TYPE = 0;", [], 1))[0]
        self._lb_datasets.Clear()
        for data_set_id, symbol in self._data_sets:
            self._lb_datasets.Append(symbol)

    def resize_datapoint_columns(self):
        width = self._dvl_datapoints.GetSize()[0]
        self._dvc_col.SetWidth(width - 30)
    
    def refresh_data_points(self):
        selection = self._lb_datasets.GetSelection()
        if selection != -1:
            data_set_id = self._data_sets[selection][0]

            self._data_points = self._datafile.query(sciplot.database.Query("SELECT DataPointID, Value FROM DataPoint WHERE DataSetID = (?);", [data_set_id], 1))[0]
            
            self._dvl_datapoints.DeleteAllItems()
            for data_point_id, value in self._data_points:
                self._dvl_datapoints.AppendItem([value])