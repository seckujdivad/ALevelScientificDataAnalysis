import wx
import wx.dataview
import typing

import forms
import sciplot.functions
import sciplot.database
import sciplot.datatable


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
        self._lb_tables.Bind(wx.EVT_LISTBOX, self._bind_lb_tables_new_selection)
        self._gbs_main.Add(self._lb_tables, wx.GBPosition(0, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        self._entry_newtable = wx.TextCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._entry_newtable, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)
        
        self._btn_add = wx.Button(self, wx.ID_ANY, "Add")
        self._btn_add.Bind(wx.EVT_BUTTON, self._bind_btn_add_clicked)
        self._gbs_main.Add(self._btn_add, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btn_remove = wx.Button(self, wx.ID_ANY, "Remove")
        self._btn_remove.Bind(wx.EVT_BUTTON, self._bind_btn_remove_clicked)
        self._gbs_main.Add(self._btn_remove, wx.GBPosition(1, 3), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._ckl_columns = wx.CheckListBox(self, wx.ID_ANY)
        self._ckl_columns.Bind(wx.EVT_CHECKLISTBOX, self._bind_ckl_columns_new_checked)
        self._ckl_columns.Bind(wx.EVT_LISTBOX, self._bind_ckl_columns_new_selection)
        self._gbs_main.Add(self._ckl_columns, wx.GBPosition(2, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        self._entry_formatstring = wx.TextCtrl(self, wx.ID_ANY)
        self._gbs_main.Add(self._entry_formatstring, wx.GBPosition(3, 1), wx.GBSpan(1, 3), wx.ALL | wx.EXPAND)

        self._btn_refresh = wx.Button(self, wx.ID_ANY, "Refresh")
        self._btn_refresh.Bind(wx.EVT_BUTTON, self._bind_btn_refresh_clicked)
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
    
    #root frame hooks
    def hook_file_opened(self):
        self.refresh_table()
        self.refresh_column_list()
        self.refresh_table_list()
    
    def hook_frame_selected(self):
        self._refresh_table()
    
    def hook_frame_unselected(self):
        self._refresh_table()
    
    #ui binds
    def _bind_btn_add_clicked(self, event):
        self._datafile.query(sciplot.database.Query("INSERT INTO `Table` (Title) VALUES ((?));", [self._entry_newtable.GetValue()], 0))
        self._entry_newtable.SetValue("")
        self.refresh_table_list()
        event.Skip()
    
    def _bind_btn_remove_clicked(self, event):
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]

            self._datafile.query([sciplot.database.Query("DELETE FROM `Table` WHERE TableID = (?);", [table_id], 0),
                                               sciplot.database.Query("DELETE FROM TableColumn WHERE TableID = (?);", [table_id], 0)])

            self.refresh_table_list()

        event.Skip()
    
    def _bind_ckl_columns_new_checked(self, event):
        self._column_selection_change()
        event.Skip()
    
    def _bind_ckl_columns_new_selection(self, event):
        self._column_selected()
        event.Skip()
    
    def _bind_lb_tables_new_selection(self, event):
        self._table_selected()
        event.Skip()
    
    def _bind_btn_refresh_clicked(self, event):
        self._refresh_table()
        event.Skip()

    #frame methods
    def refresh_table(self):
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]
            
            #remake table ui so that new columns can be added
            self._recreate_dvl_data()

            #create datatable object
            datatable = sciplot.datatable.Datatable(self._datafile)

            #set variable ids for columns
            variable_ids = []
            variable_symbols = []
            format_strings = []
            for variable_symbol, variable_id, format_string in self._datafile.query(sciplot.database.Query("SELECT Variable.Symbol, Variable.VariableID, TableColumn.FormatPattern FROM Variable INNER JOIN TableColumn ON TableColumn.VariableID = Variable.VariableID WHERE TableColumn.TableID = (?);", [table_id], 1))[0]:
                self._dvl_columns.append(self._dvl_data.AppendTextColumn(variable_symbol)) #create column header
                variable_symbols.append(variable_symbol)
                variable_ids.append(variable_id)
                format_strings.append(format_string)
            
            datatable.set_variables(variable_ids)

            #load constants for the datatable
            constants_table = {}
            for composite_unit_id, constant_symbol, constant_value in self._datafile.query(sciplot.database.Query("SELECT UnitCompositeID, Symbol, Value FROM Constant;", [], 1))[0]:
                value = sciplot.functions.Value(constant_value) #make a value object so that the data can be formatted with the format strings
                if composite_unit_id != None:
                    value.units = self._datafile.get_unit_by_id(composite_unit_id)[1]
                constants_table[constant_symbol] = constant_value
        
            #load all data from the datafile into memory
            no_exception = True
            try:
                datatable.load(constants_table)
            
            except Exception as e:
                wx.MessageBox('Couldn\'t generate table\n{}'.format(str(e)), type(e).__name__, wx.ICON_ERROR | wx.OK)
                no_exception = False

            if no_exception:
                #load transposed data
                data_as_rows = datatable.as_rows()
                
                #put data into table
                for row in data_as_rows:
                    formatted_row = []
                    for i in range(len(row)):
                        value, exponent = row[i].format(format_strings[i])
                        
                        if exponent is None: #not in exponential form, just display the value
                            formatted_row.append(value)
                        else: #exponential form, display correctly
                            if int(exponent) < 0:
                                sign = ''
                            else:
                                sign = '+'

                            formatted_row.append('{}E{}{}'.format(value, sign, exponent))

                    self._dvl_data.AppendItem(formatted_row) #add row to table
                
                #set column titles
                if len(data_as_rows) > 0:
                    for index in range(len(data_as_rows[0])):
                        column_obj = self._dvl_columns[index]
                        new_col_string = variable_symbols[index]
                        value_obj = data_as_rows[0][index]

                        unit_string = self._datafile.get_unit_string(value_obj.units)
                        
                        if unit_string != '': #add si units to title, if there are any
                            new_col_string += ': ' + unit_string
                            column_obj.SetTitle(new_col_string)
                
                #set column widths
                if len(self._dvl_columns) > 0:
                    col_width = (self._dvl_data.GetSize()[0] - 30) / len(self._dvl_columns)
                    for col in self._dvl_columns:
                        col.SetWidth(col_width)
    
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
        selection = self._ckl_columns.GetSelection()

        self._ckl_columns.Clear()
        self._columns.clear()

        variables = self._datafile.query(sciplot.database.Query("SELECT Symbol, VariableID FROM Variable", [], 1))[0]
        for variable_str, variable_id in variables:
            self._ckl_columns.Append(variable_str)
            self._columns.append((variable_id, variable_str))
        
        if selection != -1:
            self._ckl_columns.SetSelection(selection)
    
    def refresh_table_list(self):
        selection = self._lb_tables.GetSelection()

        self._tables.clear()
        self._lb_tables.Clear()

        tables = self._datafile.query(sciplot.database.Query("SELECT TableID, Title FROM `Table`", [], 1))[0]
        for table_id, table_title in tables:
            self._lb_tables.Append(table_title)
            self._tables.append((table_id, table_title))
        
        if selection != -1:
            self._lb_tables.SetSelection(selection)
    
    def _column_selection_change(self):
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]
            selected_columns_indexes = [self._columns[i][0] for i in list(self._ckl_columns.GetCheckedItems())]
            database_columns_indexes = [tup[0] for tup in self._datafile.query(sciplot.database.Query("SELECT VariableID FROM TableColumn WHERE TableID = (?);", [table_id], 1))[0]]

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
                queries.append(sciplot.database.Query("INSERT INTO TableColumn (TableID, VariableID, FormatPattern) VALUES ((?), (?), (?));", [table_id, variable_id, "*.*"], 0))
            
            for variable_id in to_remove:
                queries.append(sciplot.database.Query("DELETE FROM TableColumn WHERE VariableID = (?);", [variable_id], 0))
            
            self._datafile.query(queries)

            self.refresh_table()
    
    def _table_selected(self):
        selection_index = self._lb_tables.GetSelection()
        if selection_index != -1:
            table_id = self._tables[selection_index][0]

            #update table column selection
            columns_indexes = [tup[0] for tup in self._datafile.query(sciplot.database.Query("SELECT VariableID FROM TableColumn WHERE TableID = (?);", [table_id], 1))[0]]
            new_checked_items = []
            column_ids = [tup[0] for tup in self._columns]

            for variable_id in columns_indexes:
                new_checked_items.append(column_ids.index(variable_id))

            self._ckl_columns.SetCheckedItems(new_checked_items)

            #update displayed table data
            self.refresh_table()
    
    def _column_selected(self):
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
                self._datafile.query(sciplot.database.Query("UPDATE TableColumn SET FormatPattern = (?) WHERE VariableID = (?) AND TableID = (?);", [format_pattern, self._columns[self._column_selected_previous][0], table_id], 0))

            #load new format string if applicable
            if variable_id in selected_items:
                value = self._datafile.query(sciplot.database.Query("SELECT FormatPattern FROM TableColumn WHERE VariableID = (?) AND TableID = (?);", [variable_id, table_id], 1))
                self._entry_formatstring.SetValue(value[0][0][0])
            else:
                self._entry_formatstring.SetValue("")

            self._column_selected_previous = self._ckl_columns.GetSelection()
    
    def _refresh_table(self):
        self._column_selected()
        self._table_selected()
        self._column_selection_change()
        self.refresh_column_list()
        self.refresh_table_list()
        self.refresh_table()