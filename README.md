# ArgOS Tag Studio 🎵

**ArgOS Tag Studio** es un editor de etiquetas ID3 (metadatos) para archivos MP3, diseñado específicamente para ser ligero, rápido y funcional en entornos basados en Debian, como **ArgOS**. 

Desarrollado en Python y GTK3, permite organizar colecciones musicales grandes de forma sencilla, incluyendo la edición masiva de álbumes y portadas.

## ✨ Características

* **Edición Individual y Masiva:** Cambia el artista, álbum y portada de cientos de canciones a la vez.
* **Gestión de Portadas:** Extrae, visualiza y actualiza las imágenes internas de los archivos MP3.
* **Interfaz Nativa:** Integración perfecta con el escritorio XFCE (especialmente optimizado para el estilo de ArgOS).
* **Ligero:** Ideal para equipos con recursos limitados.
* **Atajos de Teclado:** Soporte para `Ctrl + A` para seleccionar todos los archivos rápidamente.

## 🚀 Instalación en ArgOS / Debian

La forma más sencilla de instalarlo es descargando el paquete `.deb` desde la sección de [Releases](tu-link-de-github-aca/releases).

-Una vez descargado, ejecuta en tu terminal:

sudo apt update
sudo apt install ./argostag-studio.deb

## Dependencias manuales:

Si decides correr el script directamente (argostag.py), asegúrate de tener instaladas las siguientes librerías:

sudo apt install python3-gi python3-mutagen gir1.2-gtk-3.0

## 🛠️ Desarrollo

## Este proyecto utiliza:

- Lenguaje: Python 3

- Interfaz: PyGObject (GTK3)

- Motor de Etiquetas: Mutagen

## ✒️ Autor
Tavo - Tavo78ok

Desarrollado con ❤️ para la comunidad de ArgOS.




