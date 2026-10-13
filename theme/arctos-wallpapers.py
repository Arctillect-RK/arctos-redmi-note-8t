#!/usr/bin/env python3
"""ArctOS «Обои»: pick a picture for the home screen, the lock screen or both.

Home screen  -> org.gnome.desktop.background picture-uri / picture-uri-dark (Phosh background)
Lock screen  -> org.gnome.desktop.screensaver picture-uri (patched Phosh lockscreen-bg)
"""
import os
import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

APP_ID = 'os.arctos.Wallpapers'
SEARCH_DIRS = [
    '/usr/share/wallpapers/arctos',
    os.path.expanduser('~/Pictures'),
    os.path.expanduser('~/Изображения'),
]
EXTS = ('.png', '.jpg', '.jpeg', '.webp')
THUMB_W, THUMB_H = 150, 300


def find_pictures():
    seen = set()
    for base in SEARCH_DIRS:
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for f in sorted(files):
                if f.lower().endswith(EXTS):
                    p = os.path.realpath(os.path.join(root, f))
                    if p not in seen:
                        seen.add(p)
                        yield p


class WallpaperWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Обои')
        self.set_default_size(360, 720)
        self.bg = Gio.Settings.new('org.gnome.desktop.background')
        self.lock = Gio.Settings.new('org.gnome.desktop.screensaver')

        add_btn = Gtk.Button(icon_name='list-add-symbolic', tooltip_text='Добавить фото')
        add_btn.connect('clicked', self.on_add)
        header = Adw.HeaderBar()
        header.pack_end(add_btn)

        self.flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                                min_children_per_line=2, max_children_per_line=2,
                                column_spacing=10, row_spacing=10,
                                margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        scroller = Gtk.ScrolledWindow(vexpand=True, child=self.flow)

        self.toasts = Adw.ToastOverlay(child=scroller)
        view = Adw.ToolbarView(content=self.toasts)
        view.add_top_bar(header)
        self.set_content(view)
        self.fill()

    def fill(self):
        child = self.flow.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.flow.remove(child)
            child = nxt
        for path in find_pictures():
            self.flow.append(self.make_tile(path))

    def make_tile(self, path):
        pic = Gtk.Picture.new_for_filename(path)
        pic.set_content_fit(Gtk.ContentFit.COVER)
        pic.set_size_request(THUMB_W, THUMB_H)
        frame = Gtk.Frame(child=pic)
        frame.add_css_class('card')
        btn = Gtk.Button(child=frame)
        btn.add_css_class('flat')
        btn.connect('clicked', self.on_pick, path)
        return btn

    def on_pick(self, _btn, path):
        dialog = Adw.AlertDialog(heading='Установить обои', body=os.path.basename(path))
        dialog.add_response('cancel', 'Отмена')
        dialog.add_response('home', 'Рабочий стол')
        dialog.add_response('lock', 'Экран блокировки')
        dialog.add_response('both', 'Оба')
        dialog.set_response_appearance('both', Adw.ResponseAppearance.SUGGESTED)
        dialog.set_close_response('cancel')
        dialog.connect('response', self.on_response, path)
        dialog.present(self)

    def on_response(self, _dialog, response, path):
        uri = GLib.filename_to_uri(path)
        if response in ('home', 'both'):
            self.bg.set_string('picture-uri', uri)
            self.bg.set_string('picture-uri-dark', uri)
        if response in ('lock', 'both'):
            self.lock.set_string('picture-uri', uri)
        if response != 'cancel':
            self.toasts.add_toast(Adw.Toast(title='Обои установлены'))

    def on_add(self, _btn):
        dialog = Gtk.FileDialog(title='Выбрать фото')
        flt = Gtk.FileFilter(name='Изображения')
        for e in EXTS:
            flt.add_suffix(e.lstrip('.'))
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(flt)
        dialog.set_filters(filters)
        dialog.open(self, None, self.on_add_done)

    def on_add_done(self, dialog, result):
        try:
            f = dialog.open_finish(result)
        except GLib.Error:
            return
        dest_dir = os.path.expanduser('~/Pictures/Wallpapers')
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, f.get_basename())
        f.copy(Gio.File.new_for_path(dest), Gio.FileCopyFlags.OVERWRITE, None, None, None)
        self.fill()
        self.on_pick(None, dest)


class WallpaperApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self):
        win = self.props.active_window or WallpaperWindow(self)
        win.present()


if __name__ == '__main__':
    sys.exit(WallpaperApp().run(sys.argv))
