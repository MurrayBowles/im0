""" top-level GUI """

import copy
import logging
from typing import Any, List, Tuple
import wx
#import wx.aui as aui
import wx.lib.agw.aui as aui
from wx.lib.pubsub import pub

from cfg import cfg
import db
from empty_gui import EmptyTP
from ie_gui import ImportExportTP
from tab_panel_gui import TabbedNotebook, TabPanel, TabPanelStack
from tags_gui import TagsTP
from tbl_desc import TblDesc
from tbl_descs import DbFolder_td, ImageData_td, Item_td, DbImage_td
from tbl_view import TblTP
import tbl_view_factory
from wx_task import WxSlicer

slicer = None # initialized in GuiApp.OnInit()


class GuiApp(wx.App):

    def OnInit(self):
        self.SetAppName('ImageManagement')
        cfg.restore()
        frame = GuiTop()
        frame.Show()
        self.SetTopWindow(frame)

        # pseudo-thread scheduling
        global slicer
        slicer = WxSlicer(num_queues=2, max_slice_ms=100)
        pass

        # logging
        handler = logging.FileHandler(
            wx.StandardPaths.Get().GetUserDataDir() + '\\im-log', 'w')
        #FIXME: this fails if the ImageManagement directory doesn't already exist
        handler.setLevel(logging.DEBUG)
        log_format = '%(thread)5d  %(module)-8s %(levelname)-8s %(message)s'
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.info('log file started')

        return True

menu_bar = False


class GuiTop(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(
            self, None, -1, 'Image Manager', pos=cfg.gui.pos, size=cfg.gui.size)
        self.Bind(wx.EVT_MOVE, self.on_moved)
        self.Bind(wx.EVT_SIZE, self.on_sized)

        global menu_bar
        if menu_bar:
            # menu bar
            menu_bar = wx.MenuBar()
            file_menu = wx.Menu();
            file_menu.Append(-1, 'Settings', 'Edit settings')
            exit = file_menu.Append(-1, 'Exit', 'Exit app')
            self.Bind(wx.EVT_MENU, self.on_exit, exit)
            menu_bar.Append(file_menu, 'File')
            self.SetMenuBar(menu_bar)

        # panel
        panel = self.panel = wx.Panel(self, -1)

        # notebook
        notebook = self.notebook = TabbedNotebook(panel)

        notebook.Bind(aui.EVT_AUINOTEBOOK_TAB_RIGHT_DOWN, self.on_tab_right_click)

        sizer = wx.BoxSizer()
        sizer.Add(notebook, 1, wx.EXPAND)
        panel.SetSizer(sizer)

        # status bar
        self.status_bar = self.CreateStatusBar()
        pub.subscribe(self.on_set_status, 'top.status')

    def on_moved(self, data):
        cfg.gui.pos = data.GetPosition()

    def on_sized(self, data):
        cfg.gui.size = data.GetSize()

    def on_set_status(self, data):
        logging.info('status := %s', data)
        self.status_bar.SetStatusText(data)

    def _add_push_menu_items(self, menu, tab_idx, last, fn):
        def lll(obj):
            return lambda event: fn(event, tab_idx, last, obj)
        choices = (
            [(td.menu_text(), td) for td in TblDesc.objs]
          + [(tp.cls_text(), tp) for tp in TabPanel.__subclasses__()]
        )
        choices.sort(key=lambda c: c[0])
        for x, c in enumerate(choices):
            if c[1] is EmptyTP or c[1] is TblTP:
                continue
            item = menu.Append(-1, c[0])
            self.Bind(wx.EVT_MENU, lll(c[1]), item)

    def on_tab_right_click(self, data):
        # event.Selection is the tab col_idx

        def add_item(tab_idx, x, text, fn):
            item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, lambda event: fn(event, tab_idx, x), item)

        def add_stk_item(tab_idx, stk_idx, text):
            add_item(tab_idx, stk_idx, text, self.on_stk_item_select)

        def add_ins_item(tab_idx, pos, text):
            add_item(tab_idx, pos, text, self.on_ins_item_select)

        tab_idx = data.Selection
        self.notebook.SetSelection(tab_idx)
        event = data.EventObject
        pos = event.GetPosition()
        cli_pos = self.panel.ScreenToClient(pos)
        tab_panel_stack = self.notebook.tab_panel_stacks[tab_idx]
        menu = wx.Menu()
        if tab_idx == len(self.notebook.tab_panel_stacks) - 1:
            # the right tab is the special '+' tab -- only insert to the left
            self._add_push_menu_items(menu, tab_idx, True, self.on_push_item_select)
            pass
        else:
            panel_list = tab_panel_stack.panel_list()
            if len(panel_list) > 0:
                # append the panel stack and a separator
                for (stk_idx, text) in panel_list:
                    add_stk_item(tab_idx, stk_idx, text)
                menu.AppendSeparator()
            self._add_push_menu_items(menu, tab_idx, False, self.on_push_item_select)
        self.panel.PopupMenu(menu)
        pass

    def on_stk_item_select(self, event, tab_idx, stk_idx):
        tab_panel_stack = self.notebook.tab_panel_stacks[tab_idx]
        tab_panel_stack.goto(stk_idx)
        pass

    def on_push_item_select(self, event, tab_idx, last, obj):
        if last:
            self.on_push_item_select2(event, tab_idx, -1, obj)
        else:
            def add(text, pos):
                def l(pos):
                    return lambda event: self.on_push_item_select2(event, tab_idx, pos, obj)
                item = menu.Append(-1, text)
                self.Bind(wx.EVT_MENU, l(pos), item)
            menu = wx.Menu()
            add('insert tab to left', -1)
            add('push in current tab', 0)
            add('insert tab to right', 1)
            self.PopupMenu(menu)

    def on_push_item_select2(self, event, tab_idx, pos, obj):
        add_tps = self.notebook.tab_panel_stacks[tab_idx]
        new_tps = add_tps.relative_stack(pos)
        if isinstance(obj, TblDesc):
            tbl_view_factory.get(new_tps, obj)
        else:
            obj(new_tps)

    def on_std_tab_push_item_select(self, event, tab_idx, pos, obj):
        pass

    def on_exit(self, event):
        self.Close()

def gui_test():
    app = GuiApp(False)
    app.MainLoop()
    cfg.save()

if __name__== '__main__':
    from db import open_file_db
    from base_path import dev_base_ie_source_path
    import tbl_descs
    db.session = open_file_db(dev_base_ie_source_path + '\\test.db', 'r')
    # db.open_preloaded_mem_db()
    gui_test()
