#!/usr/bin/env python3

import gi
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, error


class TagStudioWindow(Adw.ApplicationWindow):

    def __init__(self, app):
        super().__init__(application=app)

        self.files = []
        self.current_file = None

        self.set_title("ArgOS Tag Studio")
        self.set_default_size(1200, 700)

        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="ArgOS Tag Studio"))

        btn_open = Gtk.Button(label="Abrir carpeta")
        btn_open.connect("clicked", self.open_folder)

        btn_add = Gtk.Button(label="Añadir archivos")
        btn_add.connect("clicked", self.add_files)

        btn_clear = Gtk.Button(label="Limpiar lista")
        btn_clear.connect("clicked", self.clear_list)

        header.pack_start(btn_open)
        header.pack_start(btn_add)
        header.pack_start(btn_clear)

        toolbar.add_top_bar(header)

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=20,
            margin_top=20,
            margin_bottom=20,
            margin_start=20,
            margin_end=20
        )

        toolbar.set_content(main_box)

        # LISTA
        self.store = Gtk.ListStore(str, str, str, str)

        self.tree = Gtk.TreeView(model=self.store)
        self.tree.connect("cursor-changed", self.on_select)

        columns = ["Title", "Artist", "Album", "File"]

        for i, title in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_expand(True)
            self.tree.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.tree)
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)

        main_box.append(scroll)

        # PANEL DERECHO
        editor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        editor.set_size_request(320, -1)

        self.cover = Gtk.Picture()
        self.cover.set_size_request(250, 250)

        btn_cover = Gtk.Button(label="Cargar portada")
        btn_cover.connect("clicked", self.load_cover)

        editor.append(self.cover)
        editor.append(btn_cover)

        editor.append(Gtk.Label(label="Title"))
        self.entry_title = Gtk.Entry()
        editor.append(self.entry_title)

        editor.append(Gtk.Label(label="Artist"))
        self.entry_artist = Gtk.Entry()
        editor.append(self.entry_artist)

        editor.append(Gtk.Label(label="Album"))
        self.entry_album = Gtk.Entry()
        editor.append(self.entry_album)

        btn_save = Gtk.Button(label="Guardar cambios")
        btn_save.add_css_class("suggested-action")
        btn_save.connect("clicked", self.save_tags)

        editor.append(btn_save)

        main_box.append(editor)

    # LIMPIAR LISTA

    def clear_list(self, *_):

        self.store.clear()
        self.files.clear()
        self.current_file = None

        self.entry_title.set_text("")
        self.entry_artist.set_text("")
        self.entry_album.set_text("")
        self.cover.set_file(None)

    # ABRIR CARPETA

    def open_folder(self, *_):

        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, self._folder_selected)

    def _folder_selected(self, dialog, result):

        try:

            folder = dialog.select_folder_finish(result)
            path = folder.get_path()

            for file in os.listdir(path):

                if file.lower().endswith(".mp3"):

                    full = os.path.join(path, file)
                    self.add_music(full)

        except:
            pass

    # AÑADIR ARCHIVOS

    def add_files(self, *_):

        dialog = Gtk.FileDialog()
        dialog.open_multiple(self, None, self._files_selected)

    def _files_selected(self, dialog, result):

        try:

            files = dialog.open_multiple_finish(result)

            for f in files:

                path = f.get_path()

                if path and path.lower().endswith(".mp3"):
                    self.add_music(path)

        except:
            pass

    # CARGAR MUSICA

    def add_music(self, path):

        try:
            audio = EasyID3(path)
        except:
            audio = {}

        title = audio.get("title", [""])[0]
        artist = audio.get("artist", [""])[0]
        album = audio.get("album", [""])[0]

        self.files.append(path)

        self.store.append([
            title,
            artist,
            album,
            os.path.basename(path)
        ])

    # SELECCIONAR CANCION

    def on_select(self, tree):

        selection = tree.get_selection()
        model, treeiter = selection.get_selected()

        if treeiter is None:
            return

        index = model.get_path(treeiter).get_indices()[0]

        self.current_file = self.files[index]

        print("Archivo seleccionado:", self.current_file)

        try:
            audio = EasyID3(self.current_file)
        except:
            return

        title = audio.get("title", [""])[0]
        artist = audio.get("artist", [""])[0]
        album = audio.get("album", [""])[0]

        self.entry_title.set_text(title)
        self.entry_artist.set_text(artist)
        self.entry_album.set_text(album)

    # GUARDAR TAGS

    def save_tags(self, *_):

        if not self.current_file:
            return

        try:
            audio = EasyID3(self.current_file)
        except:
            audio = EasyID3()
            audio.save(self.current_file)
            audio = EasyID3(self.current_file)

        title = self.entry_title.get_text()
        artist = self.entry_artist.get_text()
        album = self.entry_album.get_text()

        audio["title"] = title
        audio["artist"] = artist
        audio["album"] = album

        audio.save()

        selection = self.tree.get_selection()
        model, iter = selection.get_selected()

        if iter:
            model.set_value(iter, 0, title)
            model.set_value(iter, 1, artist)
            model.set_value(iter, 2, album)

    # PORTADA

    def load_cover(self, *_):

        dialog = Gtk.FileDialog()
        dialog.open(self, None, self._cover_selected)

    def _cover_selected(self, dialog, result):

        try:

            file = dialog.open_finish(result)
            path = file.get_path()

            self.cover.set_file(file)

            if not self.current_file:
                return

            audio = ID3(self.current_file)

            with open(path, "rb") as img:

                audio.delall("APIC")

                audio.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=img.read()
                    )
                )

            audio.save()

        except:
            pass


class TagStudioApp(Adw.Application):

    def __init__(self):
        super().__init__(application_id="io.openargos.tagstudio")

    def do_activate(self):

        win = TagStudioWindow(self)
        win.present()


def main():

    app = TagStudioApp()
    app.run(None)


if __name__ == "__main__":
    main()
