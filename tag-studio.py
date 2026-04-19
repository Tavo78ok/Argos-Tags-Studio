#!/usr/bin/env python3

import gi
import os
import tempfile
import threading
import base64
import struct

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus


SUPPORTED_FORMATS = (".mp3", ".flac", ".ogg", ".opus")


def read_tags(path):
    """Lee los tags de un archivo de audio según su formato."""
    ext = os.path.splitext(path)[1].lower()
    tags = {"title": "", "artist": "", "album": ""}

    try:
        if ext == ".mp3":
            audio = EasyID3(path)
            tags["title"]  = audio.get("title",  [""])[0]
            tags["artist"] = audio.get("artist", [""])[0]
            tags["album"]  = audio.get("album",  [""])[0]

        elif ext == ".flac":
            audio = FLAC(path)
            tags["title"]  = (audio.get("title",  [""])  or [""])[0]
            tags["artist"] = (audio.get("artist", [""])  or [""])[0]
            tags["album"]  = (audio.get("album",  [""])  or [""])[0]

        elif ext == ".ogg":
            audio = OggVorbis(path)
            tags["title"]  = (audio.get("title",  [""])  or [""])[0]
            tags["artist"] = (audio.get("artist", [""])  or [""])[0]
            tags["album"]  = (audio.get("album",  [""])  or [""])[0]

        elif ext == ".opus":
            audio = OggOpus(path)
            tags["title"]  = (audio.get("title",  [""])  or [""])[0]
            tags["artist"] = (audio.get("artist", [""])  or [""])[0]
            tags["album"]  = (audio.get("album",  [""])  or [""])[0]

    except Exception:
        pass

    return tags


def write_tags(path, title, artist, album):
    """Escribe los tags en un archivo de audio según su formato."""
    ext = os.path.splitext(path)[1].lower()

    try:
        if ext == ".mp3":
            try:
                audio = EasyID3(path)
            except Exception:
                audio = EasyID3()
                audio.save(path)
                audio = EasyID3(path)

            if title:  audio["title"]  = title
            if artist: audio["artist"] = artist
            if album:  audio["album"]  = album
            audio.save()

        elif ext == ".flac":
            audio = FLAC(path)
            if title:  audio["title"]  = title
            if artist: audio["artist"] = artist
            if album:  audio["album"]  = album
            audio.save()

        elif ext == ".ogg":
            audio = OggVorbis(path)
            if title:  audio["title"]  = title
            if artist: audio["artist"] = artist
            if album:  audio["album"]  = album
            audio.save()

        elif ext == ".opus":
            audio = OggOpus(path)
            if title:  audio["title"]  = title
            if artist: audio["artist"] = artist
            if album:  audio["album"]  = album
            audio.save()

        return True

    except Exception:
        return False


def read_cover(path):
    """Devuelve los bytes de la portada o None."""
    ext = os.path.splitext(path)[1].lower()

    try:
        if ext == ".mp3":
            audio = ID3(path)
            for tag in audio.values():
                if isinstance(tag, APIC):
                    return tag.data

        elif ext == ".flac":
            audio = FLAC(path)
            if audio.pictures:
                return audio.pictures[0].data

        elif ext == ".opus":
            return read_cover_opus(path)

    except Exception:
        pass

    return None


def write_cover_mp3(path, cover_data, mime="image/jpeg"):
    audio = ID3(path)
    audio.delall("APIC")
    audio.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=cover_data))
    audio.save()


def write_cover_flac(path, cover_data, mime="image/jpeg"):
    audio = FLAC(path)
    audio.clear_pictures()
    pic = Picture()
    pic.type = 3
    pic.mime = mime
    pic.desc = "Cover"
    pic.data = cover_data
    audio.add_picture(pic)
    audio.save()


def _picture_to_base64(cover_data, mime="image/jpeg"):
    """Codifica una imagen en el formato METADATA_BLOCK_PICTURE para Ogg/Opus."""
    mime_bytes = mime.encode("utf-8")
    desc_bytes = b""
    header = struct.pack(
        ">IIIIII",
        3,                   # type: front cover
        len(mime_bytes),
        0,                   # description length placeholder
        0, 0,                # width, height (0 = unknown)
        0,                   # color depth
    )
    # Construcción manual del bloque
    block = (
        struct.pack(">I", 3) +
        struct.pack(">I", len(mime_bytes)) + mime_bytes +
        struct.pack(">I", len(desc_bytes)) + desc_bytes +
        struct.pack(">IIIII", 0, 0, 0, 0, len(cover_data)) +
        cover_data
    )
    return base64.b64encode(block).decode("ascii")


def _base64_to_picture_data(b64string):
    """Decodifica un METADATA_BLOCK_PICTURE y devuelve los bytes de imagen."""
    try:
        block = base64.b64decode(b64string)
        offset = 0
        _type = struct.unpack(">I", block[offset:offset+4])[0]; offset += 4
        mime_len = struct.unpack(">I", block[offset:offset+4])[0]; offset += 4
        offset += mime_len  # skip mime
        desc_len = struct.unpack(">I", block[offset:offset+4])[0]; offset += 4
        offset += desc_len  # skip description
        offset += 20        # skip width, height, depth, colors, data_length fields
        return block[offset:]
    except Exception:
        return None


def read_cover_opus(path):
    """Lee la portada de un archivo Opus."""
    try:
        audio = OggOpus(path)
        pics = audio.get("metadata_block_picture", [])
        if pics:
            return _base64_to_picture_data(pics[0])
    except Exception:
        pass
    return None


def write_cover_opus(path, cover_data, mime="image/jpeg"):
    audio = OggOpus(path)
    audio["metadata_block_picture"] = [_picture_to_base64(cover_data, mime)]
    audio.save()


def cover_to_temp(data):
    """Guarda bytes de portada en un archivo temporal y devuelve la ruta."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(data)
    tmp.close()
    return tmp.name
    """Guarda bytes de portada en un archivo temporal y devuelve la ruta."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(data)
    tmp.close()
    return tmp.name


class TagStudioWindow(Adw.ApplicationWindow):

    def __init__(self, app):
        super().__init__(application=app)

        self.set_title("ArgOS Tag Studio")
        self.set_default_size(1000, 680)

        self.files = []          # rutas únicas cargadas
        self.current_file = None
        self._cover_path = None  # ruta del icono actual en panel derecho
        self._busy = False       # bloquea operaciones concurrentes

        # ── Overlay de toasts ──────────────────────────────────────────────
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # ── ToolbarView ────────────────────────────────────────────────────
        toolbar = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar)

        # ── HeaderBar ──────────────────────────────────────────────────────
        header = Adw.HeaderBar()

        btn_folder = Gtk.Button(label="Abrir carpeta")
        btn_folder.set_tooltip_text("Ctrl+O")
        btn_folder.connect("clicked", self.open_folder)

        btn_files = Gtk.Button(label="Añadir archivos")
        btn_files.connect("clicked", self.add_files)

        btn_clear = Gtk.Button(label="Limpiar lista")
        btn_clear.connect("clicked", self.clear_list)

        sort_model = Gtk.StringList.new(["Por nombre", "Por artista", "Por álbum"])
        self.sort_combo = Gtk.DropDown(model=sort_model)
        self.sort_combo.set_tooltip_text("Ordenar lista")
        self.sort_combo.connect("notify::selected", self.on_sort_changed)

        header.pack_start(btn_folder)
        header.pack_start(btn_files)
        header.pack_start(btn_clear)
        header.pack_end(self.sort_combo)

        toolbar.add_top_bar(header)

        # ── Barra de progreso ──────────────────────────────────────────────
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        self.progress_bar.set_margin_start(12)
        self.progress_bar.set_margin_end(12)
        toolbar.add_top_bar(self.progress_bar)

        # ── Layout principal ───────────────────────────────────────────────
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        toolbar.set_content(main_box)

        # ── Lista de archivos (izquierda) ──────────────────────────────────
        list_box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        list_box_outer.set_hexpand(True)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Filtrar archivos...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        list_box_outer.append(self.search_entry)

        self.listbox = Gtk.ListBox()
        self.listbox.set_filter_func(self.filter_func)
        self.listbox.connect("row-selected", self.on_select)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.listbox)
        scroll.set_vexpand(True)
        list_box_outer.append(scroll)

        # ── Drag & Drop ────────────────────────────────────────────────────
        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.connect("drop", self.on_drop)
        self.listbox.add_controller(drop)

        main_box.append(list_box_outer)

        # ── Panel derecho (editor) ─────────────────────────────────────────
        editor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        editor.set_size_request(320, -1)

        # Portada
        self.cover = Gtk.Picture()
        self.cover.set_size_request(220, 220)
        self.cover.set_content_fit(Gtk.ContentFit.COVER)

        btn_cover = Gtk.Button(label="Cambiar portada")
        btn_cover.connect("clicked", self.change_cover)

        btn_cover_all = Gtk.Button(label="Aplicar portada a todas")
        btn_cover_all.connect("clicked", self.cover_all)

        editor.append(self.cover)
        editor.append(btn_cover)
        editor.append(btn_cover_all)

        # Campos de texto
        for label, attr in [("Título", "entry_title"),
                             ("Artista", "entry_artist"),
                             ("Álbum", "entry_album")]:
            editor.append(Gtk.Label(label=label, xalign=0))
            entry = Gtk.Entry()
            setattr(self, attr, entry)
            editor.append(entry)

        # Botones de acción
        btn_save = Gtk.Button(label="Guardar canción")
        btn_save.set_tooltip_text("Ctrl+S")
        btn_save.add_css_class("suggested-action")
        btn_save.connect("clicked", self.save_tags)

        btn_apply_all = Gtk.Button(label="Aplicar a todas")
        btn_apply_all.connect("clicked", self.apply_all)

        btn_number = Gtk.Button(label="Numerar pistas")
        btn_number.connect("clicked", self.number_tracks)

        editor.append(btn_save)
        editor.append(btn_apply_all)
        editor.append(btn_number)

        main_box.append(editor)

        # ── Atajos de teclado ──────────────────────────────────────────────
        self._setup_shortcuts(app)

    # ── Shortcuts ─────────────────────────────────────────────────────────

    def _setup_shortcuts(self, app):
        action_save = Gtk.ShortcutAction.parse_string("action(app.save)")
        action_open = Gtk.ShortcutAction.parse_string("action(app.open)")

        sc_save = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>s"), action_save)
        sc_open = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>o"), action_open)

        ctrl = Gtk.ShortcutController()
        ctrl.set_scope(Gtk.ShortcutScope.GLOBAL)
        ctrl.add_shortcut(sc_save)
        ctrl.add_shortcut(sc_open)
        self.add_controller(ctrl)

        save_action = Gtk.NamedAction.new("app.save")
        open_action = Gtk.NamedAction.new("app.open")

        from gi.repository import Gio
        a_save = Gio.SimpleAction.new("save", None)
        a_save.connect("activate", self.save_tags)
        app.add_action(a_save)

        a_open = Gio.SimpleAction.new("open", None)
        a_open.connect("activate", self.open_folder)
        app.add_action(a_open)

    # ── Utilidades UI ──────────────────────────────────────────────────────

    def toast(self, message):
        t = Adw.Toast.new(message)
        t.set_timeout(3)
        self.toast_overlay.add_toast(t)

    def show_progress(self, fraction):
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(fraction)

    def hide_progress(self):
        self.progress_bar.set_visible(False)
        self.progress_bar.set_fraction(0)

    def add_row(self, path):
        row = Gtk.ListBoxRow()
        label = Gtk.Label(label=os.path.basename(path), xalign=0)
        label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        row.set_child(label)
        row.filepath = path
        self.listbox.append(row)

    # ── Filtro y búsqueda ──────────────────────────────────────────────────

    def on_search_changed(self, entry):
        self.listbox.invalidate_filter()

    def filter_func(self, row):
        query = self.search_entry.get_text().lower()
        if not query:
            return True
        name = os.path.basename(row.filepath).lower()
        return query in name

    # ── Drag & Drop ────────────────────────────────────────────────────────

    def on_drop(self, target, value, x, y):
        files = value.get_files()
        paths = []

        for f in files:
            path = f.get_path()
            if not path:
                continue
            if os.path.isdir(path):
                for name in os.listdir(path):
                    if name.lower().endswith(SUPPORTED_FORMATS):
                        paths.append(os.path.join(path, name))
            elif path.lower().endswith(SUPPORTED_FORMATS):
                paths.append(path)

        self._load_paths(paths)
        return True

    # ── Carga de archivos ──────────────────────────────────────────────────

    def open_folder(self, *args):
        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, self.folder_selected)

    def folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            path = folder.get_path()
            paths = [
                os.path.join(path, f)
                for f in os.listdir(path)
                if f.lower().endswith(SUPPORTED_FORMATS)
            ]
            self._load_paths(paths)
        except Exception:
            pass

    def add_files(self, widget):
        filters = Gtk.FileFilter()
        filters.set_name("Audio (MP3, FLAC, OGG)")
        filters.add_pattern("*.mp3")
        filters.add_pattern("*.flac")
        filters.add_pattern("*.ogg")

        filter_list = Gio_filter_store(filters)

        dialog = Gtk.FileDialog()
        dialog.set_filters(filter_list)
        dialog.open_multiple(self, None, self.files_selected)

    def files_selected(self, dialog, result):
        try:
            files = dialog.open_multiple_finish(result)
            paths = [f.get_path() for f in files
                     if f.get_path() and f.get_path().lower().endswith(SUPPORTED_FORMATS)]
            self._load_paths(paths)
        except Exception:
            pass

    def _load_paths(self, paths):
        """Agrega archivos nuevos (sin duplicados) en hilo separado."""
        new_paths = [p for p in paths if p not in self.files]
        if not new_paths:
            self.toast("No hay archivos nuevos para agregar")
            return

        self._busy = True
        total = len(new_paths)
        self.show_progress(0)

        def worker():
            for i, path in enumerate(new_paths, 1):
                GLib.idle_add(self._add_one, path, i, total)
            GLib.idle_add(self._load_done, total)

        threading.Thread(target=worker, daemon=True).start()

    def _add_one(self, path, index, total):
        self.files.append(path)
        self.add_row(path)
        self.show_progress(index / total)
        return False

    def _load_done(self, total):
        self.hide_progress()
        self._busy = False
        self.toast(f"✓ {total} archivo{'s' if total != 1 else ''} añadido{'s' if total != 1 else ''}")
        return False

    # ── Ordenar lista ──────────────────────────────────────────────────────

    def on_sort_changed(self, combo, _):
        selected = combo.get_selected()

        if selected == 0:
            self.files.sort(key=lambda p: os.path.basename(p).lower())
        elif selected == 1:
            self.files.sort(key=lambda p: read_tags(p)["artist"].lower())
        elif selected == 2:
            self.files.sort(key=lambda p: read_tags(p)["album"].lower())

        # Reconstruir la lista visualmente
        for row in list(self.listbox):
            self.listbox.remove(row)
        for path in self.files:
            self.add_row(path)

    # ── Limpiar ────────────────────────────────────────────────────────────

    def clear_list(self, widget):
        self.files.clear()
        for row in list(self.listbox):
            self.listbox.remove(row)
        self.current_file = None
        self.entry_title.set_text("")
        self.entry_artist.set_text("")
        self.entry_album.set_text("")
        self.cover.set_filename(None)
        self.toast("Lista limpiada")

    # ── Seleccionar archivo ────────────────────────────────────────────────

    def on_select(self, box, row):
        if not row:
            return
        path = row.filepath
        self.current_file = path

        def worker():
            tags = read_tags(path)
            cover_data = read_cover(path)
            GLib.idle_add(self._apply_selection, tags, cover_data)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_selection(self, tags, cover_data):
        self.entry_title.set_text(tags["title"])
        self.entry_artist.set_text(tags["artist"])
        self.entry_album.set_text(tags["album"])

        if cover_data:
            tmp = cover_to_temp(cover_data)
            self._cover_path = tmp
            self.cover.set_filename(tmp)
        else:
            self.cover.set_filename(None)

        return False

    # ── Guardar tags ───────────────────────────────────────────────────────

    def save_tags(self, *args):
        if not self.current_file or self._busy:
            return

        title  = self.entry_title.get_text()
        artist = self.entry_artist.get_text()
        album  = self.entry_album.get_text()

        ok = write_tags(self.current_file, title, artist, album)

        if ok:
            self.toast("✓ Tags guardados")
        else:
            self.toast("⚠ Error al guardar")

    # ── Aplicar a todas ────────────────────────────────────────────────────

    def apply_all(self, widget):
        if self._busy or not self.files:
            return

        title  = self.entry_title.get_text()
        artist = self.entry_artist.get_text()
        album  = self.entry_album.get_text()

        self._busy = True
        total = len(self.files)
        self.show_progress(0)

        def worker():
            ok = 0
            for i, path in enumerate(list(self.files), 1):
                if write_tags(path, title, artist, album):
                    ok += 1
                GLib.idle_add(self.show_progress, i / total)
            GLib.idle_add(self._bulk_done, ok, total, "Tags aplicados")

        threading.Thread(target=worker, daemon=True).start()

    # ── Numerar pistas ─────────────────────────────────────────────────────

    def number_tracks(self, widget):
        if self._busy or not self.files:
            return

        self._busy = True
        total = len(self.files)
        self.show_progress(0)

        def worker():
            ok = 0
            for i, path in enumerate(list(self.files), 1):
                ext = os.path.splitext(path)[1].lower()
                try:
                    if ext == ".mp3":
                        audio = EasyID3(path)
                        audio["tracknumber"] = str(i)
                        audio.save()
                        ok += 1
                    elif ext in (".flac", ".ogg", ".opus"):
                        audio = FLAC(path) if ext == ".flac" else (OggOpus(path) if ext == ".opus" else OggVorbis(path))
                        audio["tracknumber"] = str(i)
                        audio.save()
                        ok += 1
                except Exception:
                    pass
                GLib.idle_add(self.show_progress, i / total)
            GLib.idle_add(self._bulk_done, ok, total, "Pistas numeradas")

        threading.Thread(target=worker, daemon=True).start()

    def _bulk_done(self, ok, total, action):
        self.hide_progress()
        self._busy = False
        self.toast(f"✓ {action}: {ok}/{total}")
        return False

    # ── Portada ────────────────────────────────────────────────────────────

    def change_cover(self, widget):
        if not self.current_file:
            return

        filters = Gtk.FileFilter()
        filters.set_name("Imágenes (JPG, PNG)")
        filters.add_pattern("*.jpg")
        filters.add_pattern("*.jpeg")
        filters.add_pattern("*.png")

        dialog = Gtk.FileDialog()
        dialog.open(self, None, self.cover_selected)

    def cover_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            path = file.get_path()

            ext = os.path.splitext(path)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"

            with open(path, "rb") as img:
                cover_data = img.read()

            file_ext = os.path.splitext(self.current_file)[1].lower()
            if file_ext == ".mp3":
                write_cover_mp3(self.current_file, cover_data, mime)
            elif file_ext == ".flac":
                write_cover_flac(self.current_file, cover_data, mime)
            elif file_ext == ".opus":
                write_cover_opus(self.current_file, cover_data, mime)

            self.cover.set_filename(path)
            self.toast("✓ Portada cambiada")

        except Exception:
            self.toast("⚠ Error al cambiar portada")

    def cover_all(self, widget):
        if not self.current_file or self._busy:
            return

        cover_data = read_cover(self.current_file)
        if not cover_data:
            self.toast("El archivo actual no tiene portada")
            return

        self._busy = True
        total = len(self.files)
        self.show_progress(0)

        def worker():
            ok = 0
            for i, path in enumerate(list(self.files), 1):
                ext = os.path.splitext(path)[1].lower()
                try:
                    if ext == ".mp3":
                        write_cover_mp3(path, cover_data)
                        ok += 1
                    elif ext == ".flac":
                        write_cover_flac(path, cover_data)
                        ok += 1
                    elif ext == ".opus":
                        write_cover_opus(path, cover_data)
                        ok += 1
                except Exception:
                    pass
                GLib.idle_add(self.show_progress, i / total)
            GLib.idle_add(self._bulk_done, ok, total, "Portada aplicada")

        threading.Thread(target=worker, daemon=True).start()


# ── Workaround: Gio.ListStore para el FileDialog filter ───────────────────────

def Gio_filter_store(filt):
    from gi.repository import Gio
    store = Gio.ListStore.new(Gtk.FileFilter)
    store.append(filt)
    return store


# ── Aplicación ─────────────────────────────────────────────────────────────────

class TagStudioApp(Adw.Application):

    def __init__(self):
        super().__init__(application_id="io.openargos.tagstudio")

    def do_activate(self):
        win = TagStudioWindow(self)
        win.present()


app = TagStudioApp()
app.run(None)
