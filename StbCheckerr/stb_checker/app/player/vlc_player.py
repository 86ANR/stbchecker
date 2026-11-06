import sys
import vlc
from PySide6.QtWidgets import QFrame

class VLCPlayerWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black;")
        
        # Inicializar instancia de VLC
        # --no-xlib es importante en Linux para integrarse correctamente con Qt
        self.instance = vlc.Instance("--no-xlib")
        self.media_player = self.instance.media_player_new()
        
    def _set_window_handle(self):
        """Asigna el control del vídeo de VLC al widget de PySide6"""
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.media_player.set_xwindow(self.winId())
        elif sys.platform == "win32": # for Windows
            self.media_player.set_hwnd(self.winId())
        elif sys.platform == "darwin": # for MacOS
            try:
                self.media_player.set_nsobject(int(self.winId()))
            except Exception:
                pass

    def play_url(self, url: str):
        self._set_window_handle()
        media = self.instance.media_new(url)
        self.media_player.set_media(media)
        self.media_player.play()

    def stop(self):
        self.media_player.stop()

    def pause(self):
        self.media_player.pause()

    def set_volume(self, volume: int):
        self.media_player.audio_set_volume(volume)
