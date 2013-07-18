from gi.repository import Gtk
from gtweak.tweakmodel import Tweak, TweakGroup, TWEAK_SORT_FIRST
from gtweak.widgets import GSettingsComboEnumTweak, Title

TWEAKS = (
    GSettingsComboEnumTweak("Power Button Action", "org.gnome.settings-daemon.plugins.power", "button-power", group_name="Power", sort=TWEAK_SORT_FIRST),
)

TWEAK_GROUPS = (
    TweakGroup(
        "Power",
        Title("When Laptop Lid is Closed", "Laptop Lip Closed"),
        GSettingsComboEnumTweak("On battery power","org.gnome.settings-daemon.plugins.power", "lid-close-battery-action"),
        GSettingsComboEnumTweak("When plugged in", "org.gnome.settings-daemon.plugins.power", "lid-close-ac-action"),
    ),
)
