import wx
import wx.dataview
import typing

import forms
import sciplot.functions
import sciplot.database


class DataFrame(forms.SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'data'
        self.styling_name = 'Data'
        self.styling_icon = wx.Bitmap('resources/toolbar/data.bmp')

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #create elements
        self._dvl_columns = []
        self._dvl_data = None
        self._recreate_dvl_data()

        self._lb_tables = wx.ListBox(self, wx.ID_ANY)
        self._gbs_main.Add(self._lb_tables, wx.GBPosition(0, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        self._entry_newtable = wx.TextCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._entry_newtable, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)
        
        self._btn_add = wx.Button(self, wx.ID_ANY, "Add")
        self._gbs_main.Add(self._btn_add, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove = wx.Button(self, wx.ID_ANY, "Remove")
        self._gbs_main.Add(self._btn_remove, wx.GBPosition(1, 3), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._ckl_columns = wx.CheckListBox(self, wx.ID_ANY)
        self._gbs_main.Add(self._ckl_columns, wx.GBPosition(2, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [0]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [0, 2]:
            self._gbs_main.AddGrowableRow(j)
        
        #finalise layout
        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)
    
    def _new_column_clicked(self, event):
        self._create_new_column(self._entry_new_column.GetValue())
        event.Skip()
    
    def _create_new_column(self, title):
        self._dvl_columns.append(self._dvl_data.AppendTextColumn(title))
    
    def refresh_table(self):
        self._recreate_dvl_data()

        data_table = []
        value_formatters = []
        
        for data_set_title, data_set_id, unc, uncisperc in self.subframe_share['file'].query(sciplot.database.Query("""SELECT Variable.Symbol, Variable.ID, DataSet.Uncertainty, DataSet.UncIsPerc FROM Variable INNER JOIN DataSet ON DataSet.DataSetID = Variable.ID WHERE Variable.Type = 0;""", [], 1))[0]:
            self._dvl_columns.append(self._dvl_data.AppendTextColumn(data_set_title))

            data_table.append(self.subframe_share['file'].query(sciplot.database.Query("""SELECT DataPoint.Value FROM DataPoint WHERE DataSetID = (?);""", [data_set_id], 1))[0])
            value_formatters.append(sciplot.functions.Value(0, unc, bool(uncisperc)))

        data_table_formatted = []
        for i in range(len(data_table[0])):
            data_table_formatted.append([])

            for j in range(len(data_table)):
                value_formatters[j].value = data_table[j][i][0]
                data_table_formatted[i].append('{} x 10^{} + {}'.format(*value_formatters[j].format_scientific()))

        for row in data_table_formatted:
            self._dvl_data.AppendItem(row)
    
    def _recreate_dvl_data(self):
        """
        DataViewListCtrls aren't dynamic and won't allow new columns to be added once data has been added (even if the table is empty).
        I have got around this by destroying it and recreating it whenever a new column needs to be added,
        If I see a way around this I will remove this method.
        """
        if self._dvl_data is not None:
            self._dvl_data.Destroy()
            self._dvl_columns = []
        
        self._dvl_data = wx.dataview.DataViewListCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._dvl_data, wx.GBPosition(0, 0), wx.GBSpan(3, 1), wx.ALL | wx.EXPAND)
        self.Layout()
    
    def refresh_column_list(self):
        self._ckl_columns.Clear()
        variables = [tup[0] for tup in self.subframe_share['file'].query(sciplot.database.Query("SELECT Symbol FROM Variable", [], 1))[0]]
        for variable in variables:
            self._ckl_columns.Append(variable)
    
    def refresh_table_list(self):
        self._lb_tables.Clear()
        tables = [tup[0] for tup in self.subframe_share['file'].query(sciplot.database.Query("SELECT Title FROM `Table`", [], 1))[0]]
        for table in tables:
            self._lb_tables.Append(table)
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh_table()
        self.refresh_column_list()
        self.refresh_table_list()