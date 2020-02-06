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

        self._column_selected_previous = -1

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
        self._ckl_columns.Bind(wx.EVT_LISTBOX, self._column_selected)
        self._gbs_main.Add(self._ckl_columns, wx.GBPosition(2, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        self._entry_formatstring = wx.TextCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._entry_formatstring, wx.GBPosition(3, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        self._btn_refresh = wx.Button(self, wx.ID_ANY, "Refresh")
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._refresh_table)
        self._gbs_main.Add(self._btn_refresh, wx.GBPosition(3, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

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
            
            #remake table ui so that new columns can be added
            self._recreate_dvl_data()

            #construct all functions so that trees can be evaluated
            function_table = {}
            for expression, name in self.subframe_share['file'].query(sciplot.database.Query("SELECT Expression, Symbol FROM Formula INNER JOIN Variable ON ID = FormulaID AND Type = 1", [], 1))[0]:
                function_table[name] = sciplot.functions.Function(expression)

            #get all constants
            constants_table = {key: sciplot.functions.Value(value) for value, key in self.subframe_share['file'].list_constants()}

            data_table = [] #data to be added to the table
            format_strings = [] #formatting data for each column
            dependent_data = {} #data that isn't necessarily displayed in the table, but is needed as an input for an expression that is
            
            #iterate through all columns
            for variable_symbol, variable_subid, variable_type, format_string in self.subframe_share['file'].query(sciplot.database.Query("SELECT Variable.Symbol, Variable.ID, Variable.Type, TableColumn.FormatPattern FROM Variable INNER JOIN TableColumn ON TableColumn.VariableID = Variable.VariableID WHERE TableColumn.TableID = (?);", [table_id], 1))[0]:
                self._dvl_columns.append(self._dvl_data.AppendTextColumn(variable_symbol)) #create column header

                if variable_type == 0: #dataset
                    dataset_uncertainty, dataset_uncisperc = self.subframe_share['file'].query(sciplot.database.Query("SELECT Uncertainty, UncIsPerc FROM DataSet WHERE DataSetID = (?);", [variable_subid], 1))[0][0]

                    to_add = [] #get all data points in the data set
                    for tup in self.subframe_share['file'].query(sciplot.database.Query("SELECT DataPoint.Value FROM DataPoint WHERE DataSetID = (?);", [variable_subid], 1))[0]:
                        to_add.append(sciplot.functions.Value(tup[0], dataset_uncertainty, bool(dataset_uncisperc)))

                    data_table.append(to_add)
                    format_strings.append(format_string)
                
                else: #formula
                    data_table.append(variable_symbol)
                    format_strings.append(format_string)

                    dependencies = sciplot.functions.evaluate_dependencies(variable_symbol, function_table) #get formulae and data sets that this formula depends on
                    for dependency in dependencies:
                        if (dependency in function_table) or (dependency in dependent_data) or (dependency in constants_table): #data already exists in a dependency table, so doesn't need getting from the database
                            pass
                        
                        else:
                            #get data points from the database and store
                            imported_data = self.subframe_share['file'].query(sciplot.database.Query("SELECT DataPoint.Value, DataSet.Uncertainty, DataSet.UncIsPerc FROM DataPoint INNER JOIN DataSet, Variable ON Variable.ID = DataSet.DataSetID AND DataPoint.DataSetID = DataSet.DataSetID WHERE Variable.Type = 0 AND Variable.Symbol = (?);", [dependency], 1))[0]

                            dependent_data[dependency] = []

                            for value, unc, uncisperc in imported_data:
                                dependent_data[dependency].append(sciplot.functions.Value(value, unc, bool(uncisperc)))

            #make sure all columns are the same length. if there are only formulas, determine the length that the columns should be
            data_table_formatted = []
            data_table_len = -1
            data_is_valid = True
            for data in [data for data in data_table] + [dependent_data[key] for key in dependent_data]:
                if type(data) == list:
                    if data_table_len == -1:
                        data_table_len = len(data)

                    elif len(data) == 1:
                        pass
                    
                    elif data_table_len != len(data):
                        data_is_valid = False
            
            #aggregate inputs for functions
            function_data_table = {}
            function_data_table.update(constants_table)

            if data_is_valid:
                for i in range(data_table_len):
                    data_table_formatted.append([])

                    for j in range(len(data_table)):
                        if type(data_table[j]) == list: #data set
                            value = data_table[j][i]

                        else: #function
                            #aggregate more inputs for the function from this table row
                            for dependency in dependent_data:
                                function_data_table.update({dependency: dependent_data[dependency][i]})

                            value = sciplot.functions.evaluate_tree(data_table[j], function_table, function_data_table)
                        
                        formatted_string, exponent = value.format(format_strings[j])
                        if exponent is not None:
                            formatted_string = '{}E{}'.format(formatted_string, exponent)
                        data_table_formatted[i].append(formatted_string)

                #add the formatted data to the datalistviewctrl
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
        self._entry_newtable.SetValue("")
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
    
    def _column_selection_change(self, event = None):
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

        if event is not None:
            event.Skip()
    
    def _table_selected(self, event = None):
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

        if event is not None:
            event.Skip()
    
    def _column_selected(self, event = None):
        #get selections from ui
        selection_index = self._ckl_columns.GetSelection()
        table_selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            #get ids
            variable_id = self._columns[selection_index][0]
            table_id = self._tables[table_selection_index][0]

            #get selected items - format strings only exist for selected items
            selected_items = [self._columns[index][0] for index in self._ckl_columns.GetCheckedItems()]

            #save previous format string (if it exists)
            if self._column_selected_previous != -1 and self._columns[self._column_selected_previous][0] in selected_items:
                format_pattern = self._entry_formatstring.GetValue()
                self.subframe_share['file'].query(sciplot.database.Query("UPDATE TableColumn SET FormatPattern = (?) WHERE VariableID = (?) AND TableID = (?);", [format_pattern, self._columns[self._column_selected_previous][0], table_id], 0))

            #load new format string if applicable
            if variable_id in selected_items:
                value = self.subframe_share['file'].query(sciplot.database.Query("SELECT FormatPattern FROM TableColumn WHERE VariableID = (?) AND TableID = (?);", [variable_id, table_id], 1))
                self._entry_formatstring.SetValue(value[0][0][0])
            else:
                self._entry_formatstring.SetValue("")

            self._column_selected_previous = self._ckl_columns.GetSelection()

        if event is not None:
            event.Skip()
    
    def _refresh_table(self, event = None):
        self._column_selected()
        self._table_selected()
        self._column_selection_change()
        self.refresh_column_list()
        self.refresh_table_list()
        self.refresh_table()
        
        if event is not None:
            event.Skip()
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh_table()
        self.refresh_column_list()
        self.refresh_table_list()
    
    def hook_frame_selected(self):
        self._refresh_table()
    
    def hook_frame_unselected(self):
        self._refresh_table()