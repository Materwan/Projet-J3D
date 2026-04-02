import pygame as p

p.mixer.init()


class SoundController:
    """classe pour gerer tout un son"""

    def __init__(self, path: str, loop: int | None = -1):
        self.path = path
        self.loop = loop
        self.volume = 1.0
        self.is_playing = False

    def plays_sound(self):
        """plays the sound for a duration"""
        if not self.is_playing:
            p.mixer.music.load(self.path)
            p.mixer.music.play(self.loop)
            p.mixer.music.set_volume(self.volume)
            self.is_playing = self.loop == -1

    def stop_sound(self):
        """stop the sound"""
        if self.is_playing:
            p.mixer.music.stop()
            p.mixer.music.unload()
            self.is_playing = False
        elif self.loop != -1:
            p.mixer.music.unload()

    def change_volume(self, newvol: float):
        """set the volume to the new volume"""
        if newvol > 1.0 and newvol < 0.0:
            self.volume = newvol
