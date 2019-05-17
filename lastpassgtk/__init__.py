#!/usr/bin/env python3
import json
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

    selection = None

    _entries = []

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

        entries_model = Gtk.ListStore(str, str)
        for entry in self.entries:
            entries_model.append(entry)

        completions_model = Gtk.EntryCompletion(
            model=entries_model
        )
        completions_model.set_text_column(0)

        self.selection = Gtk.ComboBox(
            visible=True,
            has_entry=True,
            model=entries_model,
            entry_text_column=-0,
            id_column=1,
        )
        self.selection.get_child().set_completion(completions_model)
        self.selection.connect('changed', self.show_selection)

        self.name = Gtk.Label(
            label='Name: ',
            visible=True,
            selectable=True,
            xalign=0,
        )
        self.url = Gtk.Label(
            label='URL: ',
            visible=True,
            use_markup=True,
            selectable=True,
            xalign=0,
        )
        self.username = Gtk.Label(
            label='Username: ',
            visible=True,
            selectable=True,
            xalign=0,
        )
        self.password = Gtk.Label(
            label='Password: ',
            visible=True,
            selectable=True,
            xalign=0,
        )
        self.note = Gtk.Label(
            label='Note: ',
            visible=True,
            use_markup=True,
            selectable=True,
            xalign=0,
        )

    def _key_press_event(self, widget, event):
        if isinstance(widget, LastPassGTKWindow) and Gdk.keyval_name(event.keyval) == 'Escape':
            self.destroy()

        if isinstance(widget, Gtk.Entry) and Gdk.keyval_name(event.keyval) == 'Return':
            self.cmd_connect(widget)

        return False

    @property
    def entries(self):
        if not self._entries:
            self._entries = []

            items = run(['/bin/sh', '-c', '/usr/bin/lpass ls --sync=now --color=never'], stdout=PIPE).stdout.decode()

            for item in items.splitlines():
                match = re.match(r'(?P<name>.+) \[id: (?P<id>\d+)\]$', item)
                if match:
                    name = match.group('name').rsplit('/', 1)[1]
                    group = match.group('name').rsplit('/', 1)[0]

                    if not name == '':
                        self._entries.append([
                            '%s (%s)' % (name, group),
                            match.group('id'),
                        ])
                else:
                    pass

                self._entries.sort()

        return self._entries

    def show_selection(self, widget):
        active_id = widget.get_active_id()
        if not active_id:
            text = widget.get_child().get_text()
            for name, i in widget.get_model():
                if text == name:
                    widget.set_active_id(i)

        if active_id:
            cmd = run(['/usr/bin/lpass', 'show', '--sync=no', '-j', active_id], stdout=PIPE)

            data = json.loads(cmd.stdout.decode())[0]

            self.name.set_label(
                f"Name: {data['name']}"
            )
            self.url.set_label(
                f"URL: <a href='{data['url']}'>{data['url']}</a>"
            )
            self.username.set_label(
                f"Username: {data['username']}"
            )
            self.password.set_label(
                f"Password: {data['password']}"
            )
            self.note.set_label(
                f"{data['note']}"
            )

    def present(self):


        vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=1,
            visible=True,
        )

        vbox.pack_start(self.selection, True, True, 0)

        vbox.pack_start(self.name, True, True, 2)
        vbox.pack_start(self.url, True, True, 2)
        vbox.pack_start(self.username, True, True, 2)
        vbox.pack_start(self.password, True, True, 2)
        vbox.pack_start(
            Gtk.Label(
                label='Note',
                visible=True,
                xalign=0,
            ), True, True, 0)

        nbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=15,
            visible=True,
            border_width=0,
        )
        nbox.pack_start(self.note, True, True, 0)

        vbox.pack_start(nbox, True, True, 0)

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
