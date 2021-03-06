#!/usr/bin/env python3
import json
import re
import sys
import os
import zenipy

from subprocess import PIPE, run

import gi

gi.require_version('Gtk', '3.0')

from os.path import expanduser
from gi.repository import (
    Gio,
    Gtk,
    Gdk
)


class LastPassGTKWindow(Gtk.ApplicationWindow):
    _history_file = expanduser('~/.rdp_history')

    selection = None

    _entries = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'application' in kwargs:
            self.application = kwargs['application']

        self.set_role('lastpass-gtk3')
        self.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_accept_focus(True)
        self.stick()
        self.resize(800, 150)

        self.set_border_width(20)
        self.set_mnemonics_visible(True)

        self.connect('key-press-event', self._key_press_event)

    def match_func(self, widget, text, tree):
        print(tree, text)


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

            self.note.get_buffer().set_text(data['note'])

    @property
    def loggedin(self):
        cmd = run(['/usr/bin/lpass', 'status'], stdout=open(os.devnull, 'w'))

        return True if cmd.returncode == 0 else False

    def login(self):
        username = zenipy.zenipy.entry(text='Please login with emailadres', placeholder='', title='', width=330, height=120, timeout=None)
        cmd = run(['/usr/bin/lpass', 'login', username])

        return True if cmd.returncode == 0 else False

    def present(self):
        vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5,
            visible=True,
        )

        if not self.loggedin:
            self.loggedin = self.login() 

        entries_model = Gtk.ListStore(str, str)
        for entry in self.entries:
            entries_model.append(entry)

        completions_model = Gtk.EntryCompletion(
            model=entries_model,
            inline_completion=True,
        )

        completions_model.set_text_column(0)
        
        self.selection = Gtk.ComboBox(
            visible=True,
            has_entry=True,
            model=entries_model,
            entry_text_column=0,
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
        self.note = Gtk.TextView(
            visible=True,
            editable=False,
            wrap_mode=True,
            monospace=True,
        )

        vbox.pack_start(self.selection, True, True, 0)
        vbox.pack_start(self.name, True, True, 0)
        vbox.pack_start(self.url, True, True, 0)
        vbox.pack_start(self.username, True, True, 0)
        vbox.pack_start(self.password, True, True, 0)
        vbox.pack_start(
            Gtk.Label(
                label='Note',
                visible=True,
                xalign=0,
            ), False, False, 0)
        scrolledwindow = Gtk.ScrolledWindow(
            visible=True,
            hexpand=True,
            vexpand=True,
            min_content_height=320
        )
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        scrolledwindow.add(self.note)

        nbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=0,
            visible=True,
            border_width=10,
        )
        nbox.pack_start(scrolledwindow, True, True, 0)

        vbox.pack_start(nbox, True, True, 0)

        self.add(vbox)

        super().present()


class LastPassGTK(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id="org.lastpass.gtk",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        self.window = None

    def do_activate(self):
        window = LastPassGTKWindow(application=self, title="LastPass RDP")
        window.present()

if __name__ == "__main__":
    app = LastPassGTK()
    app.run(sys.argv)
