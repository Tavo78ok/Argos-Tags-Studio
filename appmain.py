#!/usr/bin/env python3

import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

class TagStudio(Gtk.Window):

    def __init__(self):
        super().__init__(title="ArgOS Tag Studio - Edición Masiva")
        self.set_default_size(1100, 650)

        self.files = []
        self.current_file = None

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(main_box)

        # --- LADO IZQUIERDO (Lista) ---
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        btn_box = Gtk.Box(spacing=5)
        btn_open = Gtk.Button(label="Abrir carpeta")
        btn_open.connect("clicked", self.open_folder)

        btn_add = Gtk.Button(label="Añadir archivos")
        btn_add.connect("clicked", self.add_files)

        # NUEVO: Botón Seleccionar Todo
        btn_select_all = Gtk.Button(label="Seleccionar todo")
        btn_select_all.connect("clicked", self.select_all_files)

        btn_clear = Gtk.Button(label="Limpiar lista")
        btn_clear.connect("clicked", self.clear_list)

        btn_box.pack_start(btn_open, False, False, 0)
        btn_box.pack_start(btn_add, False, False, 0)
        btn_box.pack_start(btn_select_all, False, False, 0) # Agregado
        btn_box.pack_start(btn_clear, False, False, 0)
        left_box.pack_start(btn_box, False, False, 5)

        self.store = Gtk.ListStore(str, str, str, str)
        self.tree = Gtk.TreeView(model=self.store)

        self.selection = self.tree.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.tree.connect("cursor-changed", self.on_select)

        # NUEVO: Atajo de teclado Ctrl+A
        self.connect("key-press-event", self.on_key_press)

        columns = ["Título", "Artista", "Álbum", "Archivo"]
        for i, col_title in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_title, renderer, text=i)
            column.set_resizable(True)
            self.tree.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.tree)
        left_box.pack_start(scroll, True, True, 0)
        main_box.pack_start(left_box, True, True, 10)

        # --- LADO DERECHO (Editor) ---
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_size_request(300, -1)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        self.cover = Gtk.Image()
        self.cover.set_size_request(250, 250)
        frame.add(self.cover)
        right_box.pack_start(frame, False, False, 0)

        btn_cover = Gtk.Button(label="Cargar portada (Seleccionados)")
        btn_cover.connect("clicked", self.load_cover)
        right_box.pack_start(btn_cover, False, False, 0)

        self.entry_title = self.create_labeled_entry(right_box, "Título (Solo para uno)")
        self.entry_artist = self.create_labeled_entry(right_box, "Artista")
        self.entry_album = self.create_labeled_entry(right_box, "Álbum")

        btn_save = Gtk.Button(label="Guardar cambios en seleccionados")
        btn_save.connect("clicked", self.save_tags)
        right_box.pack_start(btn_save, False, False, 20)

        main_box.pack_start(right_box, False, False, 10)
        self.show_all()

    # --- NUEVAS FUNCIONES DE SELECCIÓN ---

    def select_all_files(self, widget):
        self.selection.select_all()

    def on_key_press(self, widget, event):
        # Si apretás Ctrl + A, se seleccionan todos
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_a:
            self.selection.select_all()
            return True
        return False

    # ------------------------------------

    def create_labeled_entry(self, container, label_text):
        container.pack_start(Gtk.Label(label=label_text, xalign=0), False, False, 0)
        entry = Gtk.Entry()
        container.pack_start(entry, False, False, 0)
        return entry

    def open_folder(self, widget):
        dialog = Gtk.FileChooserDialog(title="Seleccionar carpeta", parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            for file in sorted(os.listdir(folder)):
                if file.lower().endswith(".mp3"):
                    self.add_music(os.path.join(folder, file))
        dialog.destroy()

    def add_files(self, widget):
        dialog = Gtk.FileChooserDialog(title="Seleccionar archivos", parent=self, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        if dialog.run() == Gtk.ResponseType.OK:
            for path in dialog.get_filenames():
                if path.lower().endswith(".mp3"):
                    self.add_music(path)
        dialog.destroy()

    def add_music(self, path):
        try:
            try:
                audio = EasyID3(path)
            except ID3NoHeaderError:
                meta = ID3()
                meta.save(path)
                audio = EasyID3(path)

            title = audio.get("title", [""])[0]
            artist = audio.get("artist", [""])[0]
            album = audio.get("album", [""])[0]

            self.files.append(path)
            self.store.append([title, artist, album, os.path.basename(path)])
        except Exception as e:
            print(f"Error al cargar {path}: {e}")

    def on_select(self, tree):
        model, paths = self.selection.get_selected_rows()
        if paths:
            treeiter = model.get_iter(paths[0])
            index = paths[0][0]
            self.current_file = self.files[index]
            try:
                audio = EasyID3(self.current_file)
                # Solo llenamos los campos si hay uno solo, para no confundir
                if len(paths) == 1:
                    self.entry_title.set_text(audio.get("title", [""])[0])
                else:
                    self.entry_title.set_text("Varios archivos seleccionados...")

                self.entry_artist.set_text(audio.get("artist", [""])[0])
                self.entry_album.set_text(audio.get("album", [""])[0])
                self.update_cover_preview(self.current_file)
            except:
                pass

    def update_cover_preview(self, mp3_path):
        try:
            audio = ID3(mp3_path)
            for tag in audio.values():
                if isinstance(tag, APIC):
                    loader = GdkPixbuf.PixbufLoader()
                    loader.write(tag.data)
                    loader.close()
                    pixbuf = loader.get_pixbuf()
                    pixbuf = pixbuf.scale_simple(250, 250, GdkPixbuf.InterpType.BILINEAR)
                    self.cover.set_from_pixbuf(pixbuf)
                    return
            self.cover.clear()
        except:
            self.cover.clear()

    def save_tags(self, widget):
        model, paths = self.selection.get_selected_rows()
        if not paths: return

        t = self.entry_title.get_text()
        ar = self.entry_artist.get_text()
        al = self.entry_album.get_text()

        for path in paths:
            treeiter = model.get_iter(path)
            index = path[0]
            file_path = self.files[index]

            try:
                audio = EasyID3(file_path)
                if len(paths) == 1:
                    audio["title"] = t

                audio["artist"] = ar
                audio["album"] = al
                audio.save()

                if len(paths) == 1:
                    model.set(treeiter, 0, t, 1, ar, 2, al)
                else:
                    model.set(treeiter, 1, ar, 2, al)
            except Exception as e:
                print(f"Error en {file_path}: {e}")

        print(f"Listo: {len(paths)} archivos procesados.")

    def load_cover(self, widget):
        model, paths = self.selection.get_selected_rows()
        if not paths: return

        dialog = Gtk.FileChooserDialog(title="Seleccionar portada", parent=self, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        if dialog.run() == Gtk.ResponseType.OK:
            img_path = dialog.get_filename()
            try:
                with open(img_path, "rb") as f:
                    img_data = f.read()

                for path in paths:
                    idx = path[0]
                    audio = ID3(self.files[idx])
                    audio.delall("APIC")
                    audio.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img_data))
                    audio.save()

                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(img_path, 250, 250, True)
                self.cover.set_from_pixbuf(pixbuf)
                print(f"Portada aplicada a {len(paths)} archivos.")
            except Exception as e:
                print(f"Error portada: {e}")
        dialog.destroy()

    def clear_list(self, widget):
        self.store.clear()
        self.files = []
        self.current_file = None
        self.entry_title.set_text("")
        self.entry_artist.set_text("")
        self.entry_album.set_text("")
        self.cover.clear()

if __name__ == "__main__":
    win = TagStudio()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()
