"""Écrans de chargement, transition de carte et attente multi."""

import threading
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Manager


class GameLoadingScreen:
    """
    Écran de chargement lors de la génération du monde.
    Lance game.initialize() en arrière-plan (dans un thread).
    """

    def __init__(self, screen: pygame.Surface, manager: "Manager") -> None:
        self.manager = manager
        self.screen = screen
        self.larg, self.haut = self.screen.get_size()

        self.chargement_fini = False
        self.playing_mode: str = "solo"  # vaut soit solo, host ou guest

        self.font_title = pygame.font.SysFont("segoeui", 32, bold=True)
        self.font_body = pygame.font.SysFont("segoeui", 18)
        self.font_hint = pygame.font.SysFont("segoeui", 16)

        self.progress_bar = 0.0  # fausse barre de progression du chargement
        self.delai_time = 0.0  # fourni un delai de 500 ms pour bien voir le 100%

        self.steps = [
            (0.08, "Initialisation..."),
            (0.22, "Génération du terrain..."),
            (0.40, "Placement des ressources..."),
            (0.58, "Peuplement du monde..."),
            (0.72, "Finalisation de la carte..."),
            (0.82, "Dernières vérifications..."),
        ]

    def set_screen(self, screen: pygame.Surface):
        self.screen = screen

    def start(self, playing_mode: str):
        """Lance le chargement. playing_mode : "solo", "host" ou "guest"."""
        self.playing_mode = playing_mode
        self.chargement_fini = False
        self.progress_bar = 0.0
        self.delai_time = 0.0
        self.current_step_text = self.steps[0][1]

        threading.Thread(target=self.chargement_monde, daemon=True).start()

    def event(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.manager.running = False

    def update(self):
        dt = self.manager.clock.get_time()
        self.update_progress_bar(dt / 1000.0)

        if self.chargement_fini:
            if self.progress_bar >= 1.0:
                self.delai_time += dt
                if self.delai_time >= 500:
                    self.start_game()
            return

    def update_progress_bar(self, dt: float):
        if self.chargement_fini:
            self.progress_bar += dt * 0.8
            if self.progress_bar >= 0.995:
                self.progress_bar = 1.0
        else:
            target = 0.86
            remaining = max(target - self.progress_bar, 0.0)
            speed = 0.04 + remaining * 0.30
            self.progress_bar += dt * speed
            self.progress_bar = min(self.progress_bar, target)

        # met a jour le texte a afficher
        for i in range(len(self.steps) - 1, -1, -1):
            threshold, text = self.steps[i]
            if self.progress_bar >= threshold:
                self.current_step_text = text
                break

    def start_game(self):
        if self.playing_mode == "solo":
            self.manager.change_state("GAME")

        elif self.playing_mode == "host":
            self.manager.change_state("WAITING_GUEST")
            self.manager.states["WAITING_GUEST"].start()

        elif self.playing_mode == "guest":
            if self.manager.states["GAME"].network:
                self.manager.states["GAME"].network.set_ready()
            self.manager.change_state("GAME")

    def display(self):
        self.screen.fill((14, 14, 22))

        # titre
        title = self.font_title.render("MoleTale", True, (230, 210, 160))
        self.screen.blit(
            title, (self.larg // 2 - title.get_width() // 2, self.haut // 2 - 90)
        )

        # barre de progression :
        bx = self.larg // 2 - 200
        by = self.haut // 2 - 9

        # background de la barre
        bar_bg = pygame.Surface((400, 18), pygame.SRCALPHA)
        pygame.draw.rect(bar_bg, (40, 40, 60, 200), (0, 0, 400, 18), border_radius=8)
        self.screen.blit(bar_bg, (bx, by))

        # remplissage avec dégradé horizontal
        fill_w = max(int(400 * self.progress_bar), 0)
        if fill_w > 0:
            fill = pygame.Surface((fill_w, 18), pygame.SRCALPHA)
            for x in range(fill_w):
                ratio = x / 400
                r = int(60 + 140 * ratio)
                g = int(100 + 60 * ratio)
                b = int(220 - 60 * ratio)
                pygame.draw.line(fill, (r, g, b, 230), (x, 2), (x, 18 - 2))
            # masque coins arrondis
            mask = pygame.Surface((fill_w, 18), pygame.SRCALPHA)
            pygame.draw.rect(
                mask, (255, 255, 255, 255), (0, 0, fill_w, 18), border_radius=8
            )
            fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self.screen.blit(fill, (bx, by))

            # reflet
            shine = pygame.Surface((fill_w, 3), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 45))
            self.screen.blit(shine, (bx, by + 1))

        # bordure
        border = pygame.Surface((400, 18), pygame.SRCALPHA)
        pygame.draw.rect(
            border, (100, 100, 160, 180), (0, 0, 400, 18), width=1, border_radius=8
        )
        self.screen.blit(border, (bx, by))

        # texte d'étape (au-dessus)
        step_txt = self.font_body.render(self.current_step_text, True, (120, 120, 170))
        self.screen.blit(
            step_txt, (self.larg // 2 - step_txt.get_width() // 2, by - 34)
        )

        # pourcentage (en dessous)
        pct_txt = self.font_hint.render(
            f"{int(self.progress_bar * 100)} %", True, (180, 180, 220)
        )
        self.screen.blit(
            pct_txt, (self.larg // 2 - pct_txt.get_width() // 2, by + 18 + 10)
        )

    def chargement_monde(self) -> None:
        """Cette fonction est appelé en parrallèle pour initialiser le Game"""
        try:
            self.manager.states["GAME"].initialize()
        except Exception as exc:
            raise exc
        self.chargement_fini = True
