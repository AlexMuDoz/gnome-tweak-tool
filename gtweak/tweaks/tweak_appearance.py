import os.path

from gi.repository import Gtk
from gi.repository import GLib

import gtweak
from gtweak.tweakmodel import TWEAK_GROUP_APPEARANCE
from gtweak.widgets import DarkThemeSwitcher, GSettingsSwitchTweak, GSettingsComboTweak, Title
from gtweak.utils import walk_directories, make_combo_list_with_default

class GtkThemeSwitcher(GSettingsComboTweak):
    def __init__(self, **options):
        GSettingsComboTweak.__init__(self,
            "GTK+",
            "org.gnome.desktop.interface",
            "gtk-theme",
            make_combo_list_with_default(self._get_valid_themes(), "Adwaita"),
            **options)

    def _get_valid_themes(self):
        """ Only shows themes that have variations for gtk+-3 and gtk+-2 """
        dirs = ( os.path.join(gtweak.DATA_DIR, "themes"),
                 os.path.join(GLib.get_user_data_dir(), "themes"),
                 os.path.join(os.path.expanduser("~"), ".themes"))
        valid = walk_directories(dirs, lambda d:
                    os.path.exists(os.path.join(d, "gtk-2.0")) and \
                        os.path.exists(os.path.join(d, "gtk-3.0")))
        return valid


class IconThemeSwitcher(GSettingsComboTweak):
    def __init__(self, **options):
        GSettingsComboTweak.__init__(self,
            "Icons",
            "org.gnome.desktop.interface",
            "icon-theme",
            make_combo_list_with_default(self._get_valid_icon_themes(), "gnome"),
            **options)

    def _get_valid_icon_themes(self):
        dirs = ( os.path.join(gtweak.DATA_DIR, "icons"),
                 os.path.join(GLib.get_user_data_dir(), "icons"),
                 os.path.join(os.path.expanduser("~"), ".icons"))
        valid = walk_directories(dirs, lambda d:
                    os.path.isdir(d) and \
                        not os.path.exists(os.path.join(d, "cursors")))
        return valid

class CursorThemeSwitcher(GSettingsComboTweak):
    def __init__(self, **options):
        GSettingsComboTweak.__init__(self,
            "Cursor",
            "org.gnome.desktop.interface",
            "cursor-theme",
            make_combo_list_with_default(self._get_valid_cursor_themes(), "Adwaita"),
            **options)

    def _get_valid_cursor_themes(self):
        dirs = ( os.path.join(gtweak.DATA_DIR, "icons"),
                 os.path.join(GLib.get_user_data_dir(), "icons"),
                 os.path.join(os.path.expanduser("~"), ".icons"))
        valid = walk_directories(dirs, lambda d:
                    os.path.isdir(d) and \
                        os.path.exists(os.path.join(d, "cursors")))
        return valid
        
TWEAKS = (
    DarkThemeSwitcher(group_name=TWEAK_GROUP_APPEARANCE),
    #GSettingsSwitchTweak("org.gnome.desktop.interface", "menus-have-icons", group_name=TWEAK_GROUP_APEARANCE),
    #GSettingsSwitchTweak("org.gnome.desktop.interface", "buttons-have-icons", group_name=TWEAK_GROUP_APPEARANCE),
	Title("Theme","", group_name=TWEAK_GROUP_APPEARANCE),
	GtkThemeSwitcher(group_name=TWEAK_GROUP_APPEARANCE),
    IconThemeSwitcher(group_name=TWEAK_GROUP_APPEARANCE),
    CursorThemeSwitcher(group_name=TWEAK_GROUP_APPEARANCE),
)
