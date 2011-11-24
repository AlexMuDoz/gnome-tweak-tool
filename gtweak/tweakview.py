# This file is part of gnome-tweak-tool.
#
# Copyright (c) 2011 John Stowers
#
# gnome-tweak-tool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gnome-tweak-tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gnome-tweak-tool.  If not, see <http://www.gnu.org/licenses/>.

import logging

from gi.repository import Gtk, Gdk, GObject

import gtweak
from gtweak.tweakmodel import TweakModel

class TweakView:
    def __init__(self, builder, model):
        self._notebook = builder.get_object('notebook')
        self._detail_vbox = builder.get_object('detail_vbox')
        self._main_window = builder.get_object('main_window')

        self._main_window.set_size_request(640, 480)
        self._main_window.connect('destroy', Gtk.main_quit)

        self._entry_manager = EntryManager(
            builder.get_object('search_entry'),
            self._on_search,
            self._on_search_cancel)

        self._model = model
        self._model.load_tweaks()
        self._model.connect("row-changed", self._on_model_row_changed)

        self.treeview = Gtk.TreeView(model=model)        
        self.treeview.props.headers_visible = False
        self.treeview.append_column(
                Gtk.TreeViewColumn(
                        "Tweak", Gtk.CellRendererText(), text=TweakModel.COLUMN_NAME))
        self.treeview.get_selection().connect("changed", self._on_selection_changed)

        tweak_container = builder.get_object('tweak_container')
        self.tweak_box = Gtk.VBox(spacing=10)

        #FIXME: I may as well do this in the glade file now that
        #https://bugzilla.gnome.org/show_bug.cgi?id=644268 is fixed
        sw = Gtk.ScrolledWindow()
        sw.props.shadow_type = Gtk.ShadowType.NONE
        sw.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        vp = Gtk.Viewport()
        vp.props.shadow_type = Gtk.ShadowType.NONE
        sw.add(vp)
        vp.add(self.tweak_box)
        tweak_container.add(sw)

        #add all tweaks
        for t in self._model.tweaks:
            self._add_tweak(t)

        #dict of pending notifications, the key is the function to be called
        self._notification_functions = {}

    def _add_tweak(self, t):
        t.widget.hide()
        self.tweak_box.pack_start(t.widget, False, False, 0)
        t.set_notify_cb(self._on_tweak_notify)

    def _on_model_row_changed(self, model, path, _iter):
        logging.debug("TweakModel group changed")
        group = model.get_value(_iter, TweakModel.COLUMN_TWEAK)
        last_tweak = group.tweaks[-1]
        self._add_tweak(last_tweak)

        model, selected = self.treeview.get_selection().get_selected()
        if selected:
            if group == model.get_value(selected, TweakModel.COLUMN_TWEAK):
                last_tweak.widget.show_all()

    def run(self):
        self._main_window.show_all()
        self.hide_tweaks(self._model.tweaks)
        Gtk.main()

    def show_tweaks(self, tweaks):
        map(Gtk.Widget.show_all, [t.widget for t in tweaks])

    def hide_tweaks(self, tweaks):
        map(Gtk.Widget.hide, [t.widget for t in tweaks])

    def show_only_tweaks(self, tweaks):
        for t in self._model.tweaks:
            if t in tweaks:
                t.widget.show_all()
            else:
                t.widget.hide()

    def select_none(self):
        self.treeview.get_selection().unselect_all()

    def _on_tweak_notify_response(self, info, response, func):
        self._detail_vbox.remove(info)
        func()
        try:
            del(self._notification_functions[func])
        except KeyError:
            logging.warning("Could not remove notification function")

    def _on_tweak_notify(self, tweak, desc, error, btn, func):
        info = Gtk.InfoBar()
        info.get_content_area().add(Gtk.Label(desc))

        if error:
            info.props.message_type = Gtk.MessageType.ERROR
        else:
            info.props.message_type = Gtk.MessageType.INFO

        if btn and func:
            if func in self._notification_functions:
                return
            self._notification_functions[func] = True
            info.add_button(btn, Gtk.ResponseType.OK)
            info.connect("response", self._on_tweak_notify_response, func)
        else:
            GObject.timeout_add_seconds(2, lambda box, widget: box.remove(widget), self._detail_vbox, info)

        self._detail_vbox.pack_end(info, False, False, 0)

        info.show_all()

    def _on_search(self, txt):
        tweaks = self._model.search_matches(txt)
        self.show_only_tweaks(tweaks)
        self.select_none()
        self._notebook.set_current_page(1)

    def _on_search_cancel(self):
        self._notebook.set_current_page(0)

    def _on_pre_selection_change(self):
        self._notebook.set_current_page(0)

    def _on_post_selection_change(self):
        self._notebook.set_current_page(1)

    def _on_selection_changed(self, selection):
        model, selected = selection.get_selected()
        if selected:
            self._on_pre_selection_change()
            
            if 0:
                #apparently iters do not persist over iteration, so use treepaths instead
                path_selected = model.get_path(selected)
                #hide other tweakgroups
                root = model.get_iter_first()
                while root:
                    if model.get_path(root) != path_selected:
                        tweakgroup = model.get_value(root, model.COLUMN_TWEAK)
                        self.hide_tweaks(tweakgroup.tweaks)
                    root = model.iter_next(root)
                #show selected
                tweakgroup = model.get_value(selected, model.COLUMN_TWEAK)
                self.show_tweaks(tweakgroup.tweaks)
            else:
                tweakgroup = model.get_value(selected, model.COLUMN_TWEAK)
                self.show_only_tweaks(tweakgroup.tweaks)
            
            self._on_post_selection_change()
            
class EntryManager:

    SYMBOLIC = "-symbolic"

    def __init__(self, search_entry, search_cb, search_cancel_cb):
        self._entry = search_entry
        self._search_cb = search_cb
        self._search_cancel_cb = search_cancel_cb
        self._entry.connect("changed", self._on_changed)
        self._entry.connect("key-press-event", self._on_key_press)
        self._entry.connect("icon-release", self._on_clear_icon_release)
        self._on_changed(self._entry)

    def _search(self):
        txt = self._entry.get_text()
        if txt:
            self._search_cb(txt)

    def _search_cancel(self):
        self._search_cancel_cb()
        self._entry.set_text("")
        
    def _on_changed(self, entry):
        if not self._entry.get_text():
            self._entry.set_properties(
                    secondary_icon_name="edit-find" + EntryManager.SYMBOLIC,
                    secondary_icon_activatable=False,
                    secondary_icon_sensitive=False)
        else:
            self._entry.set_properties(
                    secondary_icon_name="edit-clear" + EntryManager.SYMBOLIC,
                    secondary_icon_activatable=True,
                    secondary_icon_sensitive=True)
    
    def _on_key_press(self, entry, event):
        if event.keyval == Gdk.KEY_Return:
            self._search()
        elif event.keyval == Gdk.KEY_Escape:
            self._search_cancel()
    
    def _on_clear_icon_release(self, *args):
        self._search_cancel()
        

