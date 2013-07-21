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

from gi.repository import Gtk

import gtweak
from gtweak.utils import AutostartManager
from gtweak.tweakmodel import TWEAK_GROUP_DESKTOP, TWEAK_GROUP_FILES
from gtweak.widgets import GSettingsSwitchTweak, GSettingsComboEnumTweak, GSettingsFileChooserButtonTweak

class DesktopIconTweak(GSettingsSwitchTweak):
    def __init__(self, **options):
        GSettingsSwitchTweak.__init__(self,
			"Icons on Desktop",
            "org.gnome.desktop.background",
            "show-desktop-icons",
            **options)

        #when the user enables nautilus to draw the desktop icons, set nautilus
        #to autostart
        self.nautilus = AutostartManager("nautilus.desktop",
                            autostart_desktop_filename="nautilus-autostart.desktop",
                            exec_cmd="nautilus -n")
        #we only need to install the desktop file on old versions of nautilus/gnome-session.
        #new ones use the new AutostartCondition and watch the gsettings key automatically
        if not self.nautilus.uses_autostart_condition("GSettings"):
            self.settings.connect('changed::'+self.key_name, self._on_setting_changed)

    def _on_setting_changed(self, setting, key):
        self.nautilus.update_start_at_login(
                self.settings.get_boolean(key))

dicons = DesktopIconTweak(group_name=TWEAK_GROUP_DESKTOP)

TWEAKS = (
    dicons,
    GSettingsSwitchTweak("Computer","org.gnome.nautilus.desktop", "computer-icon-visible", depends_on=dicons, schema_filename="org.gnome.nautilus.gschema.xml",group_name=TWEAK_GROUP_DESKTOP),
    GSettingsSwitchTweak("Home","org.gnome.nautilus.desktop", "home-icon-visible", depends_on=dicons, schema_filename="org.gnome.nautilus.gschema.xml",group_name=TWEAK_GROUP_DESKTOP),
    GSettingsSwitchTweak("Network Servers","org.gnome.nautilus.desktop", "network-icon-visible", depends_on=dicons, schema_filename="org.gnome.nautilus.gschema.xml",group_name=TWEAK_GROUP_DESKTOP),
    GSettingsSwitchTweak("Trash","org.gnome.nautilus.desktop", "trash-icon-visible", depends_on=dicons, schema_filename="org.gnome.nautilus.gschema.xml",group_name=TWEAK_GROUP_DESKTOP),
    GSettingsSwitchTweak("Mounted Volumes","org.gnome.nautilus.desktop", "volumes-visible", depends_on=dicons, schema_filename="org.gnome.nautilus.gschema.xml",group_name=TWEAK_GROUP_DESKTOP),
    #GSettingsSwitchTweak("org.gnome.nautilus.preferences", "always-use-location-entry",schema_filename="org.gnome.nautilus.gschema.xml",group_name=TWEAK_GROUP_FILES),
    #GSettingsComboEnumTweak("org.gnome.desktop.background", "picture-options", group_name=TWEAK_GROUP_DESKTOP),
    #GSettingsFileChooserButtonTweak("org.gnome.desktop.background", "picture-uri", local_only=True, mimetypes=["application/xml","image/png","image/jpeg"], group_name=TWEAK_GROUP_DESKTOP),
)
