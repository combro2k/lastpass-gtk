#!/usr/bin/env python3
import re
import sys
from subprocess import PIPE, run

import gi

gi.require_version('Gtk', '3.0')

from libqtile.command import Client
from os.path import expanduser
from gi.repository import (
    Gio,
    Gtk,
    Gdk
)


class LastPassGTKWindow(Gtk.ApplicationWindow):
    _history_file = expanduser('~/.rdp_history')
    qtile = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'application' in kwargs:
            self.application = kwargs['application']
            self.qtile = self.application.qtile

        self.set_role('lastpass-gtk3')
        self.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_accept_focus(True)
        self.stick()
        self.resize(600, 150)

        self.set_border_width(20)
        self.set_mnemonics_visible(True)

        self.connect('key-press-event', self._key_press_event)

    def _key_press_event(self, widget, event):
        if isinstance(widget, LastPassGTKWindow) and Gdk.keyval_name(event.keyval) == 'Escape':
            self.destroy()

        if isinstance(widget, Gtk.Entry) and Gdk.keyval_name(event.keyval) == 'Return':
            self.cmd_connect(widget)

        return False

    def get_lastpass_entries(self):
        entries = Gtk.ListStore(str, str)

        items = run(['/bin/sh', '-c', '/usr/bin/lpass ls --color=never'], stdout=PIPE).stdout.decode()

        for item in items.splitlines():
            match = re.match(r'(?P<name>.+) \[id: (?P<id>\d+)\]$', item)
            if match:
                entries.append([
                    match.group('id'),
                    match.group('name'),
                ])
            else:
                print(item)
                pass

        return entries

    def present(self):
        entries = self.get_lastpass_entries()

        selection = Gtk.ComboBox(
            visible=True,
            has_entry=True,
            model=entries,
            entry_text_column=1,
        )

        vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            visible=True,
        )
        vbox.pack_start(selection, True, True, 0)

        self.add(vbox)

        super().present()


class LastPassGTK(Gtk.Application):
    _qtile = None

    def __init__(self, qtile=None):
        Gtk.Application.__init__(
            self,
            application_id="org.lastpass.gtk",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        if qtile is not None:
            self._qtile = qtile

        self.window = None

    def do_activate(self):
        window = LastPassGTKWindow(application=self, title="LastPass RDP")
        window.present()

    @property
    def qtile(self):
        if self._qtile is None:
            self._qtile = Client()

        return self._qtile


if __name__ == "__main__":
    app = LastPassGTK()
    app.run(sys.argv)
