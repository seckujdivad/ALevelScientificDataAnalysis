import wx
import wx.dataview

import csv
import sys
import typing
import functools

import forms


class ImportFrame(forms.SubFrame):
    """
    UI frame for importing data from external formats
    """
    def __init__(self, parent, root_frame):
        super().__init__(parent, root_frame)

        #toolbar
        self.identifier = "import"
        self.styling_name = 'Import'
        self.styling_icon = wx.Bitmap('resources/toolbar/constants.bmp') #TODO: replace when a proper icon is made

        #set up sizer
        self._gbs_main = wx.GridBagSizer(0, 0)
        self._gbs_main.SetFlexibleDirection(wx.BOTH)
        self._gbs_main.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #create elements
        self._imported_data: typing.List[typing.List[str]] = []

        self._btn_choose_csv = wx.Button(self, wx.ID_ANY, "Import CSV")
        self._btn_choose_csv.Bind(wx.EVT_BUTTON, self._bind_btn_choose_csv_clicked)
        self._gbs_main.Add(self._btn_choose_csv, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._pnl_column_picker = wx.Panel(self, wx.ID_ANY)
        self._bs_column_picker = wx.BoxSizer(wx.HORIZONTAL)

        self._pnl_column_picker.SetSizer(self._bs_column_picker)
        self._pnl_column_picker.Layout()
        self._bs_column_picker.Fit(self._pnl_column_picker)

        self._gbs_main.Add(self._pnl_column_picker, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        self._btns_column_pickers: typing.List[wx.Button] = []

        self._dvl_data: wx.dataview.DataViewListCtrl = None #DataViewListCtrls can't have their columns dynamically changed, so this is deferred to a method (more about this in forms.frame_data.py)
        self._dvl_data_columns: typing.List[wx.dataview.DataViewColumn] = []
        self._recreate_dvl_data(False)

        self._chk_titles_are_included = wx.CheckBox(self, wx.ID_ANY, "Data contains column titles")
        self._chk_titles_are_included.Bind(wx.EVT_CHECKBOX, self._bind_chk_titles_are_included_clicked)
        self._gbs_main.Add(self._chk_titles_are_included, wx.GBPosition(3, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)

        #set sizer weights
        for i in [0]:
            self._gbs_main.AddGrowableCol(i)
        
        for j in [2]:
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
    def _bind_btn_choose_csv_clicked(self, event):
        with wx.FileDialog(self, "Open CSV", wildcard = "CSV (*.csv)|*.csv", defaultDir = sys.path[0], style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() != wx.ID_CANCEL:
                path = file_dialog.GetPath()

                with open(path, "r") as file:
                    reader = csv.reader(file)

                    self._imported_data.clear()
                    for row in reader:
                        self._imported_data.append(row)
                    
                self._display_imported_data(self._chk_titles_are_included.GetValue())

        event.Skip()
    
    def _bind_chk_titles_are_included_clicked(self, event):
        self._display_imported_data(self._chk_titles_are_included.GetValue())
        event.Skip()
    
    def _bind_btns_column_pickers_clicked(self, index, event):
        title: str = ""
        data: typing.List[str] = []
        user_interrupted_process = False

        if self._chk_titles_are_included.GetValue():
            title = self._imported_data[0][index]

            for i in range(1, len(self._imported_data)):
                data.append(self._imported_data[i][index])
        
        else:
            with wx.TextEntryDialog(self, "Name of data set", "Provide a name for the imported data set") as dialog:
                result = dialog.ShowModal()

                if result == wx.ID_CANCEL:
                    user_interrupted_process = True
                
                else:
                    title = dialog.GetValue()

                    for row in self._imported_data:
                        data.append(row[index])

        if not user_interrupted_process:
            values: typing.List[float] = []
            failed_values: typing.List[typing.Tuple[int, str]] = []
            for i in range(len(data)):
                string = data[i]
                try:
                    values.append(float(string))
                except ValueError:
                    failed_values.append((i, string))
            
            user_interrupted_process = False
            if len(failed_values) != 0:
                message = """Some imported values couldn't be converted to a floating point (decimal) representation.
This normally happens when some of the data in the table was text rather than numerical.
Pressing OK will import only those values that could be converted. Cancel will import no values.
The values (with their row indices) that couldn't be converted were:"""

                for i, failed_value in failed_values:
                    message += "\n{}: {}".format(i + 1, failed_value)

                with wx.MessageDialog(self, message, "Couldn't convert all values", wx.OK | wx.CANCEL | wx.CENTRE) as dialog:
                    if dialog.ShowModal() == wx.ID_CANCEL:
                        user_interrupted_process = True
            
            if not user_interrupted_process:
                unit_id = self._datafile.create_unit("<blank>", [])
                data_set_id = self._datafile.create_data_set(0, False, unit_id) #add a new blank data set to the database
                self._datafile.create_variable(title, 0, data_set_id)

                for value in values:
                    self._datafile.create_data_point(value, data_set_id)

                message = "Added data set '{}' containing {} item".format(title, len(values))
                if len(values) != 1:
                    message += "s"

                with wx.MessageDialog(self, message, "Data set imported", wx.OK | wx.CENTRE) as dialog:
                    dialog.ShowModal()
        
        event.Skip()

    #frame methods
    def _recreate_dvl_data(self, show_header = True):
        """
        DataViewListCtrls aren't fully dynamic, so I recreate them every time here
        See the same method in forms/frame_data.py for the same solution
        """
        if self._dvl_data is not None:
            self._dvl_data.Destroy()
        
        style = wx.dataview.DV_ROW_LINES
        if not show_header:
            style = style | wx.dataview.DV_NO_HEADER
        
        self._dvl_data = wx.dataview.DataViewListCtrl(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style)
        self._gbs_main.Add(self._dvl_data, wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.ALL | wx.EXPAND)
        self.Layout()
    
    def _display_imported_data(self, data_has_titles = True):
        self._recreate_dvl_data(data_has_titles)

        if len(self._imported_data) != 0:
            num_columns = len(self._imported_data[0])

            #determine column titles
            titles: typing.List = None
            if data_has_titles:
                titles = self._imported_data[0]
            else:
                titles = []
                for i in range(num_columns):
                    titles.append("Column {}".format(i))
            
            #create columns with appropriate titles
            self._dvl_data_columns.clear()
            for title in titles:
                column = self._dvl_data.AppendTextColumn(title, flags = 0)
                self._dvl_data_columns.append(column)
            
            #add csv data to table
            if data_has_titles:
                start_index = 1
            else:
                start_index = 0

            for row in self._imported_data[start_index:]:
                self._dvl_data.AppendItem(row)
        
            #set column widths
            column_width = self._dvl_data.GetSize()[0] / len(self._dvl_data_columns)
            for column in self._dvl_data_columns:
                column.SetWidth(column_width)
            
            #create column selection buttons
            button_num_change = num_columns - len(self._btns_column_pickers)
            if button_num_change < 0:
                for i in range(0 - button_num_change):
                    button = self._btns_column_pickers.pop(-1)
                    button.Destroy()

            elif button_num_change > 0:
                for i in range(button_num_change):
                    button = wx.Button(self._pnl_column_picker, wx.ID_ANY, "Add as dataset")
                    button.Bind(wx.EVT_BUTTON, functools.partial(self._bind_btns_column_pickers_clicked, len(self._btns_column_pickers)))
                    self._bs_column_picker.Add(button, 1)
                    self._btns_column_pickers.append(button)

            self._pnl_column_picker.Layout()
            self.Layout()