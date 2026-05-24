import pygame as p
import os
from utils import resource_path


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

    def volume_increase(self):
        """increase the volume"""
        if self.volume <= 0.9:
            self.volume += 0.1
            p.mixer.music.set_volume(self.volume)

    def volume_decrease(self):
        """decrease the volume"""
        if self.volume >= 0.1:
            self.volume -= 0.1
            p.mixer.music.set_volume(self.volume)


class SoundEffect:
    """Son court joué par-dessus la musique (utilise un canal mixer)."""

    def __init__(self, path: str, volume: float = 1.0):
        self.sound = p.mixer.Sound(path)
        self.sound.set_volume(volume)

    def play(self):
        self.sound.play()

    def set_volume(self, volume: float):
        self.sound.set_volume(volume)


SOUND_PATH = resource_path("Ressources/Musics/")

MUSIC_HOLDER = os.path.join(SOUND_PATH, "placeholder.mp3")
SOUND_AMBIANCE = os.path.join(SOUND_PATH, "ambiance.mp3")
SOUND_FOOTSTEP = os.path.join(SOUND_PATH, "footstep.mp3")
SOUND_ATTACK = os.path.join(SOUND_PATH, "attack.mp3")
EFFECT_MENU = os.path.join(SOUND_PATH, "bruit_menu.mp3")


SOUND = {
    "main_music": SoundController(MUSIC_HOLDER),
    "ambiance": SoundController(SOUND_AMBIANCE),
    "footstep": SoundController(SOUND_FOOTSTEP, 1),
    "attack": SoundController(SOUND_ATTACK, 1),
}

EFFECT = {
    "menu": SoundEffect(EFFECT_MENU, volume=0.3),
}
