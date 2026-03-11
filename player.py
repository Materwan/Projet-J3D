import pygame
from moteur import Moteur
from animations import AnimationController, create_player_animation
from typing import Tuple, Dict
import time
import asyncio
import socket
import json
import threading
import psutil


def get_netmask_for_ip(ip: str) -> str | None:
    """Donne le mask du sous-réseau"""
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == ip:
                return addr.netmask
    return None


def get_broadcast_ip(ip: str, subnet_mask: str):
    """Renvoie l'addresse pour le broadcast"""
    broadcst_ip = []
    for ip_byte, submask_byte in zip(ip.split("."), subnet_mask.split(".")):
        broadcst_ip.append(ip_byte if submask_byte == "255" else "255")

    return ".".join(broadcst_ip)


def dict_to_bytes(data: Dict) -> bytes:
    """Transforme un dictionnaire en octet pour l'envoi"""
    return bytes(json.dumps(data) + "\n", "utf-8")


def bytes_to_dict(byte: bytes) -> Dict:
    """Prend des octets et les décodes en dictionnaires"""
    if not byte:
        return None
    return json.loads(byte.decode().strip())


# Défini le port et l'addresse sur laquel broadcast
UDP_PORT = 9999
HOST_IP = socket.gethostbyname(socket.gethostname())
SUBNET_MASK = get_netmask_for_ip(HOST_IP)


class PlayerControllerBase:
    """Classe de joueur basique.\n
    Implémente les interactions et l'affichage"""

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
        self.look_direction = pygame.Vector2(0, 1)
        self.direction = "right"
        self.connected = False  # True si un invité est connecté
        self.close = False

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
        """Affiche le joueur"""

        self.animation.display((self.hitbox.x - 34, self.hitbox.y - 70))
        # pygame.draw.rect(self.screen, "red", self.hitbox, 2) # pour voir la hitbox du joueur (pas touche)


class SoloPlayerController(PlayerControllerBase):
    """Classe pour un joueur solo"""

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur | None,
        start_position: Tuple[int, int],
    ):
        # Appel le init de PlayerControllerBase, qui partage ses variables
        # avec SoloPlayerController, exemple :
        # (super().screen == self.screen) = True
        super().__init__(screen, moteur, start_position)

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
    """Classe pour un hôte de partie.\n
    Implémente les joueurs et les fonctions nécessaires ainsi
    que les fonctions de communication avec le client
    ainsi que la fonction de découverte dans les menus."""

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

        self.serveur: asyncio.Server  # pour savoir le type
        self.serveur = None  # initialise

        # Créer des processus sur d'autre thread du processeur
        # Pour le fonctionnement du serveur et du broadcast
        # Créer un event pour savoir quand broadcast
        # Démare les processus
        self.asyncio_loop = None
        self.loop = threading.Thread(target=self.initialize_tcp)
        self.loop.start()
        self.udp_prot = threading.Thread(target=self.upd_broadcast)
        self.udp_prot.start()
        self.udp_run = True

    def initialize_tcp(self):
        """Lance la fonction en thread partagé"""

        self.serveur_task = asyncio.run(self.tcp_server())

    def upd_broadcast(self):
        """Permet d'envoyer des messages au autres appareils sur le réseau
        afin qu'il puisse se connecter automatiquement"""

        print("UDP sending protocole start")

        broadcast_ip = get_broadcast_ip(HOST_IP, SUBNET_MASK)

        print(f"Broadcast on subnet mask : {broadcast_ip}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.5)

        message = bytes(
            json.dumps({"Game name": "My game", "Port": 8888}) + "\n", encoding="utf-8"
        )  # définit le message à envoyer

        while self.udp_run:  # tourne tant que le serveur n'es pas fermé
            try:
                sock.sendto(message, (broadcast_ip, UDP_PORT))
            except socket.timeout:
                pass
            if self.connected:
                self.udp_run = False
            time.sleep(0.5)

        print("UDP sending protocole stopped")

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Une instance de cette fonction est executé pour chaque joueur
        qui se connecte.\n
        La fonction vérifie que aucun joueur n'est déjà connecté, sinon la
        connexion est refusé.\n
        Il fait tourner la boucle de communication entre le serveur
        et le joueur"""

        def get_to_send_data() -> Dict:
            return {
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

        # Si un au client est connecté
        if self.connected:
            writer.close()
            return

        # Si aucun autre client n'est connecté
        print("Joueur connecté")
        self.connected = True

        # Arrêt le serveur : n'accepte plus les connections
        self.serveur.close()
        print("Serveur fermé")

        # Défini les variables à envoyer
        to_send_data = get_to_send_data()
        writer.write(dict_to_bytes(to_send_data))
        await writer.drain()

        try:
            while True:

                # Si le jeu est fermé, envoie l'info au client et ferme la connexion
                if self.close:
                    writer.write(dict_to_bytes({"close": True}))
                    await writer.drain()
                    break

                # Récupère les données, les décodes et verifie leur existence
                recieved_bytes = await asyncio.wait_for(reader.readline(), timeout=1.0)
                recieved_data = bytes_to_dict(recieved_bytes)
                if not recieved_bytes:
                    break

                # Si le client ferme son jeu, ferme le jeu et la connexion
                if recieved_data["close"] == True:
                    print("Le client a fermé la connexion")
                    self.close = True
                    break

                # Met à jour les varibles
                self.guest.velocity.update(recieved_data["guest"]["velocity"])
                self.guest.moving_intent = recieved_data["guest"]["moving_intent"]
                self.guest.direction = recieved_data["guest"]["direction"]

                # Défini les variables à envoyer et les encodes
                to_send_data = get_to_send_data()
                to_send_bytes = dict_to_bytes(to_send_data)

                # Envoie les données
                writer.write(to_send_bytes)
                await writer.drain()

                # Attend de manière à envoyer seulement 30 fois par secondes
                await asyncio.sleep(1 / 30)
        finally:
            # Ferme la connexion
            writer.close()
            print("Connexion fermé")

    async def tcp_server(self):
        """Lance le server et donc autorise le client à se connecter;"""

        self.asyncio_loop = asyncio.get_running_loop()
        # Défini un serveur sur le port 8888
        self.serveur = await asyncio.start_server(
            self.handle_client, host="0.0.0.0", port=8888
        )

        # Lance le serveur qui s'execute tant que
        # le jeu tourne et que le client est connecté
        print("Attente de client")
        async with self.serveur:
            try:
                await self.serveur.serve_forever()
            except asyncio.CancelledError:
                print("Serveur fermé")

    def stop_server(self):
        """Arrête le protocole de commuinication avec le client."""

        async def stop_server():
            if self.serveur and self.serveur.is_serving():
                self.serveur.close()
                await self.serveur.wait_closed()

        asyncio.run_coroutine_threadsafe(stop_server(), self.asyncio_loop)

    def update(self):

        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:  # Si le joueur veux bouger

            self.look_direction = self.velocity.normalize()

            self.moteur.collision(self.hitbox, self.velocity, self.guest.hitbox)

            super().update()

        if self.guest.moving_intent:  # Si le client veux bouger

            self.moteur.collision(self.guest.hitbox, self.guest.velocity, self.hitbox)
            self.guest.update()

        self.animation.update(self.moving_intent, self.direction)
        self.guest.animation.update(self.guest.moving_intent, self.guest.direction)

    def display(self):
        """Affiche le joueur ainsi que l'invité"""

        super().display()
        self.guest.display()


class GuestController(PlayerControllerBase):
    """Classe pour un client.\n
    Implémente les joueurs et les fonctions nécessaires ainsi
    que les fonction de communications avec l'hôte."""

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur | None,
        start_position: Tuple[int, int],
        address: str,
        port: int,
    ):

        super().__init__(screen, moteur, start_position)
        # Défini un player pour l'hôte
        self.host = PlayerControllerBase(self.screen, moteur, start_position)

        self.address = address
        self.port = port

        # Défini un processus pour la connexion
        # sur un autre thread du processeur
        self.loop = threading.Thread(target=self.run)
        self.loop.start()

    async def connect(self):
        """Se connecte au serveur"""

        self.reader, self.writer = await asyncio.open_connection(
            self.address, self.port
        )

        # Récupère la position initiale des joueurs
        recieved_bytes = await self.reader.readline()
        recieved_data = bytes_to_dict(recieved_bytes)

        # Met à jour les variable correspondantes
        self.position.update(recieved_data["guest"]["position"])
        self.host.position.update(recieved_data["host"]["position"])
        self.host.moving_intent = recieved_data["host"]["moving_intent"]
        self.host.direction = recieved_data["host"]["direction"]

        # Met à jour la position des hitbox
        self.hitbox.topleft = self.position
        self.host.hitbox.topleft = self.host.position
        self.host.update()

    async def initialize(self):
        """Fonction de lancement du réseau"""

        await self.connect()
        await self.handle_host()

    def run(self):
        """Lance le serveur en se connectant à l'hôte puis
        en lancant le processus de communication"""

        asyncio.run(self.initialize())

    async def handle_host(self):
        """Gére les communications entre le client et l'hôte."""

        def get_to_send_data() -> Dict:
            return {
                "guest": {
                    "velocity": list(self.velocity),
                    "moving_intent": self.moving_intent,
                    "direction": self.direction,
                },
                "close": False,
            }

        try:
            while True:

                # Si le jeu est fermé, envoyer l'info à l'hôte et ferme la connexion
                if self.close:
                    self.writer.write(dict_to_bytes({"close": True}))
                    await self.writer.drain()
                    break

                # Défini les variables à envoyer à l'hôte et les encodes
                to_send_data = get_to_send_data()
                to_send_bytes = dict_to_bytes(to_send_data)

                # Envoie les données
                self.writer.write(to_send_bytes)
                await self.writer.drain()

                # Récupère les donnée les décode et verifie leur existence
                recieved_bytes = await asyncio.wait_for(
                    self.reader.readline(), timeout=1.0
                )
                recieved_data = bytes_to_dict(recieved_bytes)
                if not recieved_data:
                    break

                # Si l'hôte a fermé son jeu, fermer le jeu
                if recieved_data["close"] is True:
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
            self.writer.close()
            print("Connexion fermé")

    def update(self):

        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:  # Si le joueur veux bouger

            self.look_direction = self.velocity.normalize()

            super().update()

        if self.host.moving_intent:  # Si l'hôte veux bouger

            self.host.update()
            self.host.hitbox.topleft = self.host.position

        self.animation.update(self.moving_intent, self.direction)
        self.host.animation.update(self.host.moving_intent, self.host.direction)

    def display(self):
        """Affiche le joueur ainsi que l'hôte"""

        super().display()
        self.host.display()
