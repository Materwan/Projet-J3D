import sys
import os


def resource_path(relative_path: str) -> str:
    """Résout un chemin de ressource par rapport à l'exécutable (ou au script)."""
    if getattr(sys, "frozen", False):
        # Mode exécutable (PyInstaller, cx_Freeze, etc.)
        base = os.path.dirname(sys.executable)
    else:
        # Mode script Python normal
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)
