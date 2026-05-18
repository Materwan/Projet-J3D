import sys
import os
from typing import List
from abc import ABC, abstractmethod
import pygame


def resource_path(relative_path: str) -> str:
    """Résout un chemin de ressource par rapport à l'exécutable (ou au script)."""
    if getattr(sys, "frozen", False):
        # Mode exécutable (PyInstaller, cx_Freeze, etc.)
        base = os.path.dirname(sys.executable)
    else:
        # Mode script Python normal
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


class DefaultManager(ABC):
    screen: pygame.Surface

    @abstractmethod
    def event(self, events: List[pygame.event.Event]):
        """Gére les évenements : interactions du joueur avec l'interface."""

    @abstractmethod
    def update(self):
        """Met à jour les éléments de l'interface."""

    @abstractmethod
    def display(self):
        """Affiche les éléments correspondant à l'interface."""
