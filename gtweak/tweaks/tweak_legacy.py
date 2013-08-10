# This file is part of gnome-tweak-tool.
# Copyright (c) 2012 Red Hat, Inc.
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
#
# Authors:
#       Rui Matos

import logging

from gi.repository import Pango, Gtk, GnomeDesktop
from gtweak.gshellwrapper import GnomeShellFactory
from gtweak.tweakmodel import Tweak, TweakGroup, TWEAK_GROUP_WINDOWS, TWEAK_GROUP_TYPING, TWEAK_GROUP_MOUSE, TWEAK_GROUP_FILES, TWEAK_GROUP_DESKTOP, TWEAK_GROUP_FONTS, TWEAK_GROUP_POWER, TWEAK_GROUP_WORKSPACES, TWEAK_SORT_FIRST
from gtweak.widgets import GSettingsSwitchTweak, build_label_beside_widget, GSettingsFileChooserButtonTweak, GSettingsComboEnumTweak, GSettingsSpinButtonTweak, GSettingsComboTweak, build_horizontal_sizegroup
from gtweak.gsettings import GSettingsSetting, GSettingsMissingError, GSettingsFakeSetting

_shell = GnomeShellFactory().get_shell()
_shell_loaded = _shell is not None

class _XkbOption(Gtk.Box, Tweak):
    def __init__(self, group_id, parent_settings, xkb_info, **options):
        try:
            desc = xkb_info.description_for_group(group_id)
        except AttributeError:
            desc = group_id
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        Tweak.__init__(self, desc, desc, **options)

        self._group_id = group_id
        self._parent_settings = parent_settings
        self._xkb_info = xkb_info
        self._value = None
        self._possible_values = []

        model_values = [(None, _("Disabled"))]
        for option_id in self._xkb_info.get_options_for_group(group_id):
            desc = self._xkb_info.description_for_option(group_id, option_id)
            model_values.append((option_id, desc))
            self._possible_values.append(option_id)

        store = Gtk.ListStore(str, str)
        store.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        for (val, name) in model_values:
            store.append((val, name))

        self._combo = Gtk.ComboBox(model = store)
        renderer = Gtk.CellRendererText()
        renderer.props.ellipsize = Pango.EllipsizeMode.END
        renderer.props.max_width_chars = 40
        self._combo.pack_start(renderer, True)
        self._combo.add_attribute(renderer, "text", 1)
        self._combo_changed_handler_id = self._combo.connect("changed", self._on_combo_changed)

        build_label_beside_widget(self.name, self._combo, hbox=self)
        self.widget_for_size_group = self._combo

        self.reload()

    def reload(self):
        for v in self._parent_settings.get_strv(TypingTweakGroup.XKB_GSETTINGS_NAME):
            if (v in self._possible_values):
                self._value = v
                self._update_combo()
                return

        self._value = None
        self._update_combo()

    def _update_combo(self):
        model = self._combo.get_model()
        for row in model:
            if self._value == row[0]:
                self._combo.disconnect(self._combo_changed_handler_id)
                self._combo.set_active_iter(row.iter)
                self._combo_changed_handler_id = self._combo.connect("changed", self._on_combo_changed)
                break

    def _on_combo_changed(self, combo):
        new_value = combo.get_model().get_value(combo.get_active_iter(), 0)

        if not new_value:
            if self._value:
                self._parent_settings.setting_remove_from_list(TypingTweakGroup.XKB_GSETTINGS_NAME, self._value)
        else:
            if self._value:
                self._parent_settings.setting_remove_from_list(TypingTweakGroup.XKB_GSETTINGS_NAME, self._value)
            self._parent_settings.setting_add_to_list(TypingTweakGroup.XKB_GSETTINGS_NAME, new_value)

class TypingTweakGroup(TweakGroup):

    XKB_GSETTINGS_SCHEMA = "org.gnome.desktop.input-sources"
    XKB_GSETTINGS_NAME = "xkb-options"
    # These are configurable in gnome-control-center
    XKB_OPTIONS_BLACKLIST = {"lv3","Compose key"}

    def __init__(self):
        TweakGroup.__init__(self, TWEAK_GROUP_TYPING)
        self._option_objects = []

        ok = False
        try:
            self._kbdsettings = GSettingsSetting(self.XKB_GSETTINGS_SCHEMA)
            self._kbdsettings.connect("changed::"+self.XKB_GSETTINGS_NAME, self._on_changed)
            self._xkb_info = GnomeDesktop.XkbInfo()
            ok = True
        except GSettingsMissingError:
            logging.info("Typing missing schema %s" % self.XKB_GSETTINGS_SCHEMA)
        except AttributeError:
            logging.warning("Typing missing GnomeDesktop.gir with Xkb support")
        finally:
            if ok:
                for opt in set(self._xkb_info.get_all_option_groups()) - self.XKB_OPTIONS_BLACKLIST:
                    self._option_objects.append(
                            _XkbOption(opt, self._kbdsettings, self._xkb_info)
                    )

        self.set_tweaks(*self._option_objects)

    def _on_changed(self, *args):
        for obj in self._option_objects:
            obj.reload()

sg = build_horizontal_sizegroup()

TWEAK_GROUPS = (
    TypingTweakGroup(),
)

TWEAKS = (
    GSettingsSwitchTweak("Show All Sources",
                         "org.gnome.desktop.input-sources",
                         "show-all-sources",
                         logout_required=True,
                         group_name=TWEAK_GROUP_TYPING),
    GSettingsSwitchTweak("Show location of pointer",
                         "org.gnome.settings-daemon.peripherals.mouse", 
                         "locate-pointer", 
                         schema_filename="org.gnome.settings-daemon.peripherals.gschema.xml", 
                         group_name=TWEAK_GROUP_MOUSE),
    GSettingsSwitchTweak("Use location entry", "org.gnome.nautilus.preferences", "always-use-location-entry",schema_filename="org.gnome.nautilus.gschema.xml",group_name=TWEAK_GROUP_FILES),
    GSettingsFileChooserButtonTweak("org.gnome.desktop.background", "picture-uri", local_only=True, mimetypes=["application/xml","image/png","image/jpeg"], group_name=TWEAK_GROUP_DESKTOP),
    GSettingsComboEnumTweak("Background options","org.gnome.desktop.background", "picture-options", group_name=TWEAK_GROUP_DESKTOP),
    GSettingsSpinButtonTweak("org.gnome.desktop.interface", "text-scaling-factor", adjustment_step=0.1, digits=1,group_name=TWEAK_GROUP_FONTS),
    GSettingsComboTweak("Modifier to use for modified window click actions",
                        "org.gnome.desktop.wm.preferences",
                        "mouse-button-modifier",
                        [("disabled", _("Disabled")), ("<Alt>", "Alt"), ("<Super>", "Super")],
                        group_name=TWEAK_GROUP_WINDOWS),   
    GSettingsSwitchTweak("Whether to resize with the right button","org.gnome.desktop.wm.preferences", "resize-with-right-button", group_name=TWEAK_GROUP_WINDOWS),
    GSettingsSwitchTweak("Whether rasing should be a side-effect of other user interactions","org.gnome.desktop.wm.preferences", "raise-on-click", group_name=TWEAK_GROUP_WINDOWS),
    GSettingsSwitchTweak("Attach modal dialog to the parent window","org.gnome.mutter", "attach-modal-dialogs", group_name=TWEAK_GROUP_WINDOWS),
    GSettingsSwitchTweak("Laptop lid, when closed, will suspend even if there is an external monitor plugged in","org.gnome.settings-daemon.plugins.power", "lid-close-suspend-with-external-monitor", group_name=TWEAK_GROUP_POWER),
    GSettingsComboEnumTweak("Whether to turn off specific monitors after boot","org.gnome.settings-daemon.plugins.xrandr", "default-monitors-setup", size_group=sg, group_name=TWEAK_GROUP_WORKSPACES),
    GSettingsSwitchTweak("Workspaces only on primary monitor","org.gnome.mutter", "workspaces-only-on-primary", schema_filename="org.gnome.shell.gschema.xml", loaded=_shell_loaded, group_name=TWEAK_GROUP_WORKSPACES), 
)
