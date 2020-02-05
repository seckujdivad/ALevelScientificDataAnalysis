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

        self._tables = []
        self._columns = []

        self._lb_tables = wx.ListBox(self, wx.ID_ANY)
        self._lb_tables.Bind(wx.EVT_LISTBOX, self._table_selected)
        self._gbs_main.Add(self._lb_tables, wx.GBPosition(0, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        self._entry_newtable = wx.TextCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._entry_newtable, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)
        
        self._btn_add = wx.Button(self, wx.ID_ANY, "Add")
        self._btn_add.Bind(wx.EVT_BUTTON, self._add_table)
        self._gbs_main.Add(self._btn_add, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove = wx.Button(self, wx.ID_ANY, "Remove")
        self._btn_remove.Bind(wx.EVT_BUTTON, self._remove_table)
        self._gbs_main.Add(self._btn_remove, wx.GBPosition(1, 3), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._ckl_columns = wx.CheckListBox(self, wx.ID_ANY)
        self._ckl_columns.Bind(wx.EVT_CHECKLISTBOX, self._column_selection_change)
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
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]
            
            self._recreate_dvl_data()

            function_table = {}
            for expression, name in self.subframe_share['file'].query(sciplot.database.Query("SELECT Expression, Symbol FROM Formula INNER JOIN Variable ON ID = FormulaID AND Type = 1", [], 1))[0]:
                function_table[name] = sciplot.functions.Function(expression)

            constants_table = {key: sciplot.functions.Value(value) for value, key in self.subframe_share['file'].list_constants()}

            data_table = []
            value_formatters = []
            dependent_data = {}
            
            for variable_symbol, variable_subid, variable_type, format_string in self.subframe_share['file'].query(sciplot.database.Query("""SELECT Variable.Symbol, Variable.ID, Variable.Type, TableColumn.FormatPattern FROM Variable INNER JOIN TableColumn ON TableColumn.VariableID = Variable.VariableID WHERE TableColumn.TableID = (?);""", [table_id], 1))[0]:
                self._dvl_columns.append(self._dvl_data.AppendTextColumn(variable_symbol))

                if variable_type == 0:
                    dataset_uncertainty, dataset_uncisperc = self.subframe_share['file'].query(sciplot.database.Query("SELECT Uncertainty, UncIsPerc FROM DataSet WHERE DataSetID = (?);", [variable_subid], 1))[0][0]
                    data_table.append([tup[0] for tup in self.subframe_share['file'].query(sciplot.database.Query("""SELECT DataPoint.Value FROM DataPoint WHERE DataSetID = (?);""", [variable_subid], 1))[0]])
                    value_formatters.append((sciplot.functions.Value(0, dataset_uncertainty, bool(dataset_uncisperc)), format_string))
                
                else:
                    data_table.append(variable_symbol)
                    value_formatters.append((None, format_string))

                    dependencies = sciplot.functions.evaluate_dependencies(variable_symbol, function_table)
                    for dependency in dependencies:
                        if (dependency in function_table) or (dependency in dependent_data) or (dependency in constants_table):
                            pass
                        
                        else:
                            imported_data = self.subframe_share['file'].query(sciplot.database.Query("SELECT DataPoint.Value, DataSet.Uncertainty, DataSet.UncIsPerc FROM DataPoint INNER JOIN DataSet, Variable ON Variable.ID = DataSet.DataSetID AND DataPoint.DataSetID = DataSet.DataSetID WHERE Variable.Type = 0 AND Variable.Symbol = (?);", [dependency], 1))[0]

                            dependent_data[dependency] = []

                            for value, unc, uncisperc in imported_data:
                                dependent_data[dependency].append(sciplot.functions.Value(value, unc, bool(uncisperc)))

            data_table_formatted = []
            data_table_len = -1
            data_is_valid = True
            for data in [data for data in data_table] + [dependent_data[key] for key in dependent_data]:
                print(data)
                if type(data) == list:
                    if data_table_len == -1:
                        data_table_len = len(data)

                    elif len(data) == 1:
                        pass
                    
                    elif data_table_len != len(data):
                        data_is_valid = False
            
            function_data_table = {}
            function_data_table.update(constants_table)

            if data_is_valid:
                print(data_table_len)
                for i in range(data_table_len):
                    data_table_formatted.append([])

                    for j in range(len(data_table)):
                        if type(data_table[j]) == list:
                            value_formatters[j][0].value = data_table[j][i]
                            data_table_formatted[i].append(value_formatters[j][0].format(value_formatters[j][1])[0])

                        else:
                            for dependency in dependent_data:
                                function_data_table.update({dependency: dependent_data[dependency][i]})

                            data_table_formatted[i].append(sciplot.functions.evaluate_tree(data_table[j], function_table, function_data_table).format(value_formatters[j][1])[0])

                for row in data_table_formatted:
                    self._dvl_data.AppendItem(row)
            
            else:
                wx.MessageBox("Not all columns are the same length\nRemove all offending columns", "Column length error", wx.ICON_ERROR | wx.OK)
    
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
        self._columns.clear()

        variables = self.subframe_share['file'].query(sciplot.database.Query("SELECT Symbol, VariableID FROM Variable", [], 1))[0]
        for variable_str, variable_id in variables:
            self._ckl_columns.Append(variable_str)
            self._columns.append((variable_id, variable_str))
    
    def refresh_table_list(self):
        self._tables.clear()
        self._lb_tables.Clear()

        tables = self.subframe_share['file'].query(sciplot.database.Query("SELECT TableID, Title FROM `Table`", [], 1))[0]
        for table_id, table_title in tables:
            self._lb_tables.Append(table_title)
            self._tables.append((table_id, table_title))
    
    def _add_table(self, event):
        self.subframe_share['file'].query(sciplot.database.Query("INSERT INTO `Table` (Title) VALUES ((?));", [self._entry_newtable.GetValue()], 0))
        self.refresh_table_list()
        event.Skip()
    
    def _remove_table(self, event):
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]

            self.subframe_share['file'].query([sciplot.database.Query("DELETE FROM `Table` WHERE TableID = (?);", [table_id], 0),
                                               sciplot.database.Query("DELETE FROM TableColumn WHERE TableID = (?);", [table_id], 0)])

            self.refresh_table_list()

        event.Skip()
    
    def _column_selection_change(self, event):
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]
            selected_columns_indexes = [self._columns[i][0] for i in list(self._ckl_columns.GetCheckedItems())]
            database_columns_indexes = [tup[0] for tup in self.subframe_share['file'].query(sciplot.database.Query("SELECT VariableID FROM TableColumn WHERE TableID = (?);", [table_id], 1))[0]]

            to_add = []
            to_remove = []

            for i in selected_columns_indexes:
                if i not in database_columns_indexes:
                    to_add.append(i)
            
            for i in database_columns_indexes:
                if i not in selected_columns_indexes:
                    to_remove.append(i)
            
            queries = []
            for variable_id in to_add:
                queries.append(sciplot.database.Query("INSERT INTO TableColumn (TableID, VariableID, FormatPattern) VALUES ((?), (?), (?));", [table_id, variable_id, ""], 0))
            
            for variable_id in to_remove:
                queries.append(sciplot.database.Query("DELETE FROM TableColumn WHERE VariableID = (?);", [variable_id], 0))
            
            self.subframe_share['file'].query(queries)

            self.refresh_table()

        event.Skip()
    
    def _table_selected(self, event):
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]

            #update table column selection
            columns_indexes = [tup[0] for tup in self.subframe_share['file'].query(sciplot.database.Query("SELECT VariableID FROM TableColumn WHERE TableID = (?);", [table_id], 1))[0]]
            new_checked_items = []
            column_ids = [tup[0] for tup in self._columns]

            for variable_id in columns_indexes:
                new_checked_items.append(column_ids.index(variable_id))

            self._ckl_columns.SetCheckedItems(new_checked_items)

            #update displayed table data
            self.refresh_table()

        event.Skip()
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh_table()
        self.refresh_column_list()
        self.refresh_table_list()