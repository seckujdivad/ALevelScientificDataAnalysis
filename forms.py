import wx
import wx.dataview
import typing

import sciplot.database
import sciplot.functions


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
    
    def hook_file_opened(self):
        """
        Method called by root frame when a file is opened. Should be overwritten by inheriting class
        """


class DataFrame(SubFrame):
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

        for i in range(1):
            self._gbs_main.AddGrowableCol(i)
        
        for j in range(2):
            self._gbs_main.AddGrowableRow(j)

        #create elements
        
        self._dvl_columns = []
        self._dvl_data = None
        self._recreate_dvl_data()

        self._entry_new_column = wx.TextCtrl(self, wx.ID_ANY)
        self._entry_new_column.SetMaxSize(wx.DefaultSize)
        self._entry_new_column.SetMinSize(wx.DefaultSize)

        self._gbs_main.Add(self._entry_new_column, wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_new_column = wx.Button(self, wx.ID_ANY, "New Column")
        self._btn_new_column.Bind(wx.EVT_BUTTON, self._new_column_clicked)
        self._gbs_main.Add(self._btn_new_column, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)
        
        #finalise layout
        self.SetSizer(self._gbs_main)
        self.Layout()
        self._gbs_main.Fit(self)
    
    def _new_column_clicked(self, event):
        self._create_new_column(self._entry_new_column.GetValue())
        event.Skip()
    
    def _create_new_column(self, title):
        self._dvl_columns.append(self._dvl_data.AppendTextColumn(title))
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh_table()
    
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
            print(row)
    
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
        self._gbs_main.Add(self._dvl_data, wx.GBPosition(0, 0), wx.GBSpan(2, 1), wx.ALL | wx.EXPAND)
        self.Layout()


class GraphFrame(SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'graph'
        self.styling_name = 'Graph'
        self.styling_icon = wx.Bitmap('resources/toolbar/graph.bmp')


class FormulaeFrame(SubFrame):
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = 'formulae'
        self.styling_name = 'Formulae'
        self.styling_icon = wx.Bitmap('resources/toolbar/formulae.bmp')


class TablesFrame(SubFrame):
    pass


class ConstantsFrame(SubFrame):
    pass


manifest: typing.List[SubFrame] = [DataFrame, GraphFrame, FormulaeFrame]# TablesFrame, , ConstantsFrame]