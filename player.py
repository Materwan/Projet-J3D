import pygame
from moteur import Moteur
from animations import AnimationController, create_player_animation
from typing import Tuple, Dict
import time
import asyncio
import socket
import json
import threading

UDP_IP = socket.gethostbyname(socket.gethostname())
UDP_PORT = 9999


class PlayerControllerBase:

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur | None,
        start_position: Tuple[int, int],
    ):
        """Créer les éléments nécessaires à un joueur"""

        self.screen = screen
        self.moteur = moteur
        self.guest: PlayerControllerBase
        self.moving_intent = False

        # Initialise les animations
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            (100, 100),
        )
        self.animation = AnimationController(animation_images, self.screen)

        # Initialise les données nécessaires pour un joueur
        self.keybinds = None
        self.keybinds: Dict
        self.position = pygame.Vector2(start_position)
        self.hitbox = pygame.Rect(start_position[0], start_position[1], 32, 15)
        self.velocity = pygame.Vector2(0, 0)
        self.direction = "right"
        self.connected = False

    def event(self, keys: Tuple[bool]):
        """
        Détermine le vecteur de mouvement à partir des entrées clavier.

        Utilise une soustraction binaire pour calculer la direction :
        - (1 - 0) = 1  (Droite/Bas)
        - (0 - 1) = -1 (Gauche/Haut)
        - (1 - 1) ou (0 - 0) = 0 (Neutre)

        Le vecteur 'self.velocity' ainsi mis à jour contient des composantes
        x et y allant de -1 à 1, permettant aussi la gestion des diagonales.
        """

        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]],
        )

    def update_animation(self):
        """Update the direction of the animation"""

        self.look_direction = self.velocity.normalize()

        if self.velocity.x < 0:
            self.direction = "left"
        elif self.velocity.x > 0:
            self.direction = "right"
        """ Optionnel : en attente animation up et down
        elif self.velocity.y > 0:
            self.host_data["direction"] = "down"
        elif self.velocity.y < 0:
            self.host_data["direction"] = "up"
        """

    def update(self):
        """Met à jour toutes les données en lien avec le moteur"""

        is_moving = self.velocity.length_squared()
        if is_moving > 0:  # si on se deplace toujours alors :

            # gestion des déplacements en diagonales
            if is_moving > 1:
                self.velocity.normalize_ip()  # [1, 1] devient [0.707107, 0.707107]

            # gestion du vecteur position
            self.position += self.velocity * 2
            # la position de la hitbox se cale sur le vecteur position
            self.hitbox.topleft = self.position

            self.update_animation()

    def display(self):

        self.animation.display((self.hitbox.x - 34, self.hitbox.y - 70))
        # pygame.draw.rect(self.screen, "red", self.hitbox, 2) # pour voir la hitbox du joueur (pas touche)


class SoloPlayerController(PlayerControllerBase):

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur | None,
        start_position: Tuple[int, int],
    ):

        super().__init__(screen, moteur, start_position)

    def event(self, keys: Tuple[bool]):

        return super().event(keys)

    def update(self):

        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:  # si le joueur veut se deplacer alors :

            self.look_direction = self.velocity.normalize()

            self.moteur.collision(self.hitbox, self.velocity, None)
            super().update()

        self.animation.update(self.moving_intent, self.direction)

    def display(self):

        super().display()


class HostController(PlayerControllerBase):

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur | None,
        start_position: Tuple[int, int],
    ):

        super().__init__(screen, moteur, start_position)

        # Initialise les données de l'invité
        self.guest = PlayerControllerBase(self.screen, moteur, (200, 200))
        self.recieved_data = {"Guest": {"velocity": [0, 0]}}

        self.serveur: asyncio.Server
        self.serveur = None
        self.connected = False  # True si un invité est connecté
        self.close = False

        self.loop = threading.Thread(target=self.initialize_tcp)
        self.loop.start()
        self.udp_prot = threading.Thread(target=self.upd_broadcast)
        self.udp_event = threading.Event()
        self.udp_prot.start()
        self.udp_event.set()
        """self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.tcp_server())
        self.loop.run_forever()"""
        # asyncio.run(self.initialize())

    def initialize_tcp(self):

        self.serveur_task = asyncio.run(self.tcp_server())

    def upd_broadcast(self):
        """A modifier"""
        message = bytes(json.dumps({"Game name": "My game", "Port": 8888}) + "\n", encoding="utf-8")

        print("UDP sending protocole start")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP

        while not self.close:
            if self.udp_event.is_set():
                sock.sendto(message, (UDP_IP, UDP_PORT))
                print("Send")
                time.sleep(0.5)
        
        print("UDP sending protocole stopped")
        sock.close()

    def event(self, keys: Tuple[bool]):

        super().event(keys)

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):

        # Si un au client est connecté
        if self.connected:
            writer.close()
            return

        # Si aucun autre client n'est connecté
        print("Joueur connecté")
        self.connected = True

        # Arrêt le serveur : n'accepte plus les connections
        self.serveur.close()
        self.udp_event.clear()
        print("Serveur fermé")

        try:
            while True:

                # Si le jeu est fermé, envoie l'info au client et ferme la connexion
                if self.close:
                    writer.write(bytes(json.dumps({"close": True}) + "\n", "utf-8"))
                    await writer.drain()
                    break

                # Récupère les données et verifi leur existence
                recieved_bytes = await reader.readline()
                if not recieved_bytes:
                    break

                # Decode les donnée en un dictionnaire
                recieved_str = recieved_bytes.decode().strip()
                recieved_data = json.loads(recieved_str)

                # Si le client ferme son jeu, ferme le jeu et la connexion
                if recieved_data["close"] == True:
                    print("Le client a fermé la connexion")
                    self.close = True
                    break

                # Met à jour les varibles
                self.guest.velocity.update(recieved_data["guest"]["velocity"])
                self.guest.moving_intent = recieved_data["guest"]["moving_intent"]
                self.guest.direction = recieved_data["guest"]["direction"]

                # Défini les variables à envoyer
                to_send_data = {
                    "guest": {
                        "position": list(self.guest.position),
                        "velocity": list(self.guest.velocity),
                    },
                    "host": {
                        "position": list(self.position),
                        "moving_intent": self.moving_intent,
                        "direction": self.direction,
                    },
                    "close": False,
                }
                # Tranformer les variables en bits
                to_send_bytes = bytes(json.dumps(to_send_data) + "\n", "utf-8")

                # Envoie les données
                writer.write(to_send_bytes)
                await writer.drain()

                # Attend de manière à envoyer seulement 30 fois par secondes
                await asyncio.sleep(1 / 30)
        finally:
            writer.close()
            print("Connexion fermé")

    async def tcp_server(self):

        self.serveur = await asyncio.start_server(
            self.handle_client, host="0.0.0.0", port=8888
        )

        print("Attente de client")
        async with self.serveur:
            try:
                await self.serveur.serve_forever()
            except asyncio.CancelledError:
                print("Serveur fermé")

    def update(self):

        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:

            self.look_direction = self.velocity.normalize()

            self.moteur.collision(self.hitbox, self.velocity, self.guest.hitbox)

            super().update()

        if self.guest.moving_intent:

            self.moteur.collision(self.guest.hitbox, self.guest.velocity, self.hitbox)
            self.guest.update()

        self.animation.update(self.moving_intent, self.direction)
        self.guest.animation.update(self.guest.moving_intent, self.guest.direction)

    def display(self):
        """Affiche le joueur ainsi que l'invité"""

        super().display()
        self.guest.display()


class GuestController(PlayerControllerBase):

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur | None,
        start_position: Tuple[int, int],
        adresse: asyncio.StreamReader,
        port: asyncio.StreamWriter,
    ):

        super().__init__(screen, moteur, start_position)
        self.host = PlayerControllerBase(self.screen, moteur, start_position)

        self.adresse = adresse
        self.port = port
        self.close = False

        self.loop = threading.Thread(target=self.run)
        self.loop.start()
        """self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.initialize())
        self.loop.run_forever()"""
        # asyncio.run(self.initialize())

    async def connect(self):

        self.reader, self.writer = await asyncio.open_connection(
            self.adresse, self.port
        )

    def run(self):

        asyncio.run(self.initialize())

    async def initialize(self):

        await self.connect()
        await self.handle_host()

    def event(self, keys: Tuple[bool]):

        super().event(keys)

    async def handle_host(self):

        try:
            while True:

                # Si le jeu est fermé, envoyer l'info à l'hôte et ferme la connexion
                if self.close:
                    self.writer.write(
                        bytes(json.dumps({"close": True}) + "\n", "utf-8")
                    )
                    await self.writer.drain()
                    break

                # Défini les variables à envoyer à l'hôte
                to_send_data = {
                    "guest": {
                        "velocity": list(self.velocity),
                        "moving_intent": self.moving_intent,
                        "direction": self.direction,
                    },
                    "close": False,
                }
                # Tranforme les données en bits
                to_send_bytes = bytes(json.dumps(to_send_data) + "\n", "utf-8")

                # Envoie les données
                self.writer.write(to_send_bytes)
                await self.writer.drain()

                # Récupère les donnée et verifie leur existence
                recieved_bytes = await self.reader.readline()
                if not recieved_bytes:
                    break

                # Transforme les donnée en dictionnaire
                recieved_str = recieved_bytes.decode().strip()
                recieved_data = json.loads(recieved_str)

                # Si l'hôte a fermé son jeu, fermer le jeu
                if recieved_data["close"] == True:
                    self.close = True
                    print("L'hôte a fermé la connexion")
                    break

                # Met à jour les variables
                self.position.update(recieved_data["guest"]["position"])
                self.velocity.update(recieved_data["guest"]["velocity"])
                self.host.position.update(recieved_data["host"]["position"])
                self.host.moving_intent = recieved_data["host"]["moving_intent"]
                self.host.direction = recieved_data["host"]["direction"]

                # Attend de manière à ce qu'il y ai 30 envoie par secondes
                await asyncio.sleep(1 / 30)
        finally:
            print("Connexion fermé")

    def update(self):

        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:

            self.look_direction = self.velocity.normalize()

            super().update()

        if self.host.moving_intent:

            self.host.update()
            self.host.hitbox.topleft = self.host.position

        self.animation.update(self.moving_intent, self.direction)
        self.host.animation.update(self.host.moving_intent, self.host.direction)

    def display(self):
        """Affiche le joueur ainsi que l'hôte"""

        super().display()
        self.host.display()
