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
import glob
import os.path

import gtweak
from gtweak.utils import SchemaList, LogoutNotification, Notification
from gi.repository import Gtk

def N_(x): return x

TWEAK_GROUP_APPEARANCE = N_("Appearance")
TWEAK_GROUP_DESKTOP = N_("Desktop")
TWEAK_GROUP_EXTENSION = N_("Extensions")
TWEAK_GROUP_FONTS = N_("Fonts")
TWEAK_GROUP_KEYBOARD = N_("Keyboard Layout")
TWEAK_GROUP_POWER = N_("Power")
TWEAK_GROUP_APPLICATION = N_("Startup Applications")
TWEAK_GROUP_TOPBAR = N_("Top Bar")
TWEAK_GROUP_WINDOWS = N_("Windows")
TWEAK_GROUP_WORKSPACES = N_("Workspaces")

TWEAK_GROUP_MOUSE = N_("Mouse")
TWEAK_GROUP_TYPING = N_("Typing")
TWEAK_GROUP_FILES = N_("Files")

TWEAK_SORT_FIRST = -1e3
TWEAK_SORT_LAST = 1e3

LOG = logging.getLogger(__name__)

class Tweak(object):

    main_window = None
    widget_for_size_group = None

    def __init__(self, name, description, **options):
        self.name = name
        self.description = description
        self.uid = options.get("uid", self.__class__.__name__)
        self.group_name = options.get("group_name",_("Miscellaneous"))
        self.loaded = options.get("loaded", True)

        self._search_cache = None

    def search_matches(self, txt):
        if self._search_cache == None:
            self._search_cache = self.name.lower() + " " + self.description.lower()
        return  txt in self._search_cache

    def notify_logout(self):
        self._logoutnotification = LogoutNotification()

    def notify_information(self, summary, desc=""):
        self._notification = Notification(summary, desc)

class TweakGroup(object):

    main_window = None

    def __init__(self, name, *tweaks, **options):
        self.name = name
        self.tweaks = [t for t in tweaks if t.loaded]
        self.uid = options.get('uid', self.__class__.__name__)

class TweakModel(Gtk.ListStore):
    (COLUMN_NAME,
     COLUMN_TWEAK) = range(2)

    def __init__(self):
        super(TweakModel, self).__init__(str, object)
        self._tweak_dir = gtweak.TWEAK_DIR
        assert(os.path.exists(self._tweak_dir))

        self.set_sort_column_id(self.COLUMN_NAME, Gtk.SortType.ASCENDING)

        # map of tweakgroup.name -> tweakgroup
        self._tweak_group_names = {}
        self._tweak_group_iters = {}

    @property
    def tweaks(self):
        return (t for row in self for t in row[TweakModel.COLUMN_TWEAK].tweaks)

    @property
    def tweak_groups(self):
        return (row[TweakModel.COLUMN_TWEAK] for row in self)

    def load_tweaks(self, main_window):
        tweak_files = [
                os.path.splitext(os.path.split(f)[-1])[0]
                    for f in glob.glob(os.path.join(self._tweak_dir, "tweak_group_*.py"))]

        if not gtweak.ENABLE_TEST:
            try:
                tweak_files.remove("tweak_group_test")
            except ValueError:
                pass
        
        if not gtweak.ALL_TWEAKS:
            try:
                tweak_files.remove("tweak_legacy")
            except ValueError:
                pass
        
        groups = []
        tweaks = []

        mods = __import__("gtweak.tweaks", globals(), locals(), tweak_files, 0)
        for mod in [getattr(mods, file_name) for file_name in tweak_files]:
            groups.extend( getattr(mod, "TWEAK_GROUPS", []) )
            
        schemas = SchemaList() 
   
        for g in groups:
            g.main_window = main_window
            if g.tweaks:
                self.add_tweak_group(g)
                for i in g.tweaks:
                    i.main_window = main_window
                    try:
                        schemas.insert(i.key_name, i.schema_name)
                    except:
                        pass

    def add_tweak_group(self, tweakgroup):
        if tweakgroup.name in self._tweak_group_names:
            LOG.critical("Tweak group named: %s already exists" % tweakgroup.name)
            return

        _iter = self.append([gettext(tweakgroup.name), tweakgroup])
        self._tweak_group_names[tweakgroup.name] = tweakgroup
        self._tweak_group_iters[tweakgroup.name] = _iter

    def search_matches(self, txt):
        tweaks = []                                          
        groups = []                                                             
        
        for g in self.tweak_groups:
            for t in  g.tweaks:                                             
                if t.search_matches(txt): 
                    tweaks.append(t)
                    if not g.name in groups:                          
                        groups.append(g.name)
        return tweaks, groups 

    def get_tweakgroup_iter(self, name):
        return self._tweak_group_iters[name]
        
