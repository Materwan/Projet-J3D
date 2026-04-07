"""Module pour la gestion du joueur en solo/multi"""

from typing import Tuple, Dict, Any
import time
import asyncio
import socket
import json
import threading
import psutil

import pygame

from moteur import Moteur
from map import Map
from camera_system import Camera
from animations import AnimationController


UDP_PORT = 9999
SPEED = 3


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


class PlayerControllerBase:
    """Classe de joueur basique.

    Implémente les interactions et l'affichage"""

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur,
        map: Map,
        start_position: Tuple[int, int],
    ):
        """Initialise les éléments nécessaires à un joueur"""

        # -- Controlleur --
        self.screen = screen
        self.camera: Camera | None = None
        self.moteur = moteur
        self.map = map
        if moteur is not None and map is not None:
            self.moteur.map = map

        self.show_hitbox = False  # pour F2

        # -- Animations --
        self.animation = AnimationController(
            r"Ressources\Animations\Player", (100, 100), self.screen
        )
        self.im_size = pygame.Vector2(self.animation.im_size)

        # -- Joueur --
        self.keybinds: Dict | None = None
        self.position = pygame.Vector2(start_position)
        self.hitbox = pygame.Rect(0, 0, 28, 15)
        self.hitbox.center = self.position
        self.velocity = pygame.Vector2(0, 0)
        self.direction = "right"
        self.moving_intent = False

        # -- Attaque --
        self.attaque = False
        self.attaque_rect = None

        # -- Réseau --
        self.close = False

    def set_camera(self, camera: Camera):
        """Initialise la camera du joueur et du client si besoin."""

    def toggle_hitbox(self):
        """Change debug F2."""

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

    def update_direction(self):
        """Update the direction of the animation"""

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

    def update_motor(self):
        """Met à jour toutes les données en lien avec le moteur"""

        mov = self.velocity.length_squared()
        if mov > 0:  # Si mouvement

            if mov > 1:  # Si en diagonale
                self.velocity.normalize_ip()

            self.position += self.velocity * SPEED  # Modif pos

            self.hitbox.center = self.position  # Place hitbox sur pos

    def authority_update(self, collision_hitbox: list[pygame.Rect] = []):
        """Met à jour les donnée d'un controlleur autoritaire (Solo / Host)."""

        # -- Mouvements --
        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:  # Si le joueur veux bouger

            self.update_direction()

            self.moteur.collision(self.hitbox, self.velocity, collision_hitbox)

            self.update_motor()  # Update vitesse

        # -- Animation --
        state = "run" if self.moving_intent else "idle"
        if self.attaque and self.animation.current_state != "attack":
            state = "attack"
            self.attaque_rect = self.moteur.create_rect_attaque(
                self.position, self.direction
            )
            self.attaque = False  # Bloque anti spam

        self.animation.update(state, self.direction)

    def display(self):
        """Affiche tous les éléments avec la camera."""

        # -- Joueur --
        screen_pos = pygame.Vector2(
            self.camera.apply(self.hitbox).center
        )  # La caméra convertit la position en position écran
        self.animation.display(
            screen_pos - pygame.Vector2(self.im_size[0] // 2, self.im_size[1] - 22)
        )  # -22 pour afficher le joueur un peu au dessus de la hitbox

        # -- Debug F2 --
        if self.show_hitbox:
            pygame.draw.rect(self.screen, "red", self.camera.apply(self.hitbox), 2)
            # -- Box Joueur --
            if self.attaque_rect and self.animation.current_state == "attack":
                pygame.draw.rect(
                    self.screen, "red", self.camera.apply(self.attaque_rect), 2
                )
            # -- Box Environnement --
            for obstacle in self.moteur.nearby_obstacles:
                pygame.draw.rect(self.screen, "red", self.camera.apply(obstacle), 2)


class SoloPlayerController(PlayerControllerBase):
    """Classe pour un joueur solo"""

    def set_camera(self, camera: Camera):
        self.camera = camera

    def toggle_hitbox(self):
        self.show_hitbox = not self.show_hitbox

    def update(self):
        """Met à jour les éléments nécessaire du joueur."""

        # -- Map --
        self.map.load_chunks(self.position)

        # -- Joueur --
        self.authority_update()


class HostController(PlayerControllerBase):
    """Classe pour un hôte de partie.

    Implémente les joueurs et les fonctions nécessaires ainsi
    que les fonctions de communication avec le client
    ainsi que la fonction de découverte dans les menus."""

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur,
        map: Map,
        start_position: Tuple[int, int],
    ):
        """Initialise les données du joueur et du protocole réseau
        dans un thread en parallèle."""

        # -- Joueur --
        super().__init__(screen, moteur, map, start_position)

        # -- Invité --
        self.guest = PlayerControllerBase(
            self.screen, moteur, self.map, (start_position[0] + 50, start_position[1])
        )

        # -- Réseau --
        self.serveur: asyncio.Server | None = None
        self.connected = False
        self.ip = socket.gethostbyname(socket.gethostname())
        self.subnet_mask = get_netmask_for_ip(self.ip)

        # -- Ennemis --
        self.ennemis_data: Dict[int, Dict[str, Any]]

        # -- Processus --
        self.asyncio_loop: asyncio.AbstractEventLoop | None = None
        self.loop = threading.Thread(target=self.initialize_tcp)
        self.loop.start()
        self.udp_prot = threading.Thread(target=self.upd_broadcast)
        self.udp_prot.start()
        self.udp_run = True

    def set_camera(self, camera: Camera):
        self.camera = camera
        self.guest.camera = camera

    def toggle_hitbox(self):
        self.show_hitbox = not self.show_hitbox
        self.guest.show_hitbox = self.show_hitbox

    def initialize_tcp(self):
        """Lance la fonction en thread partagé."""
        asyncio.run(self.tcp_server())

    def upd_broadcast(self):
        """Permet d'envoyer des messages au autres appareils sur le réseau
        afin qu'il puisse se connecter automatiquement"""

        print("UDP sending protocole start")

        # -- Setup variables --
        broadcast_ip = get_broadcast_ip(self.ip, self.subnet_mask)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.5)

        message = dict_to_bytes(
            {"Game name": "My game", "Port": 8888, "last": time.time()}
        )  # définit le message à envoyer

        print(f"Broadcast on subnet mask : {broadcast_ip}")

        # -- Envoi --
        while self.udp_run:  # tourne tant que le serveur n'es pas fermé
            try:
                sock.sendto(message, (broadcast_ip, UDP_PORT))
            except socket.timeout:
                pass
            if self.connected or self.close:
                self.udp_run = False
            time.sleep(0.5)

        print("UDP sending protocole stopped")

    def get_to_send_data(self, *include: str) -> Dict:
        """Créer le dictionnaire de valeurs à envoyer au client."""
        dic = {
            "guest": {
                "position": list(self.guest.position),
                "attaque_rect": (
                    list(self.guest.attaque_rect)
                    if self.guest.attaque_rect
                    and self.guest.animation.current_state == "attack"
                    else None
                ),
            },
            "host": {
                "position": list(self.position),
                "moving_intent": self.moving_intent,
                "velocity": list(self.velocity),
                "direction": self.direction,
                "attaque": self.animation.current_state == "attack",
                "attaque_rect": (
                    list(self.attaque_rect)
                    if self.attaque_rect and self.animation.current_state == "attack"
                    else None
                ),
            },
            "ennemis": self.ennemis_data,
            "close": False,
        }
        if "map" in include:
            dic["map"] = {
                "nb_chunks": self.map.nb_chunks.tolist(),
                "chunk_size": self.map.chunk_size_tile.tolist(),
                "octaves": self.map.octaves,
                "seed": self.map.seed,
            }
        return dic

    def update_variables(self, data: Dict):
        """Met à jour toutes les variables reçu par le client."""
        self.guest.velocity = self.moteur.verif_velocity(
            data["guest"]["velocity"]
        )  # verification de la vélocité dès qu'on le recoit
        self.guest.moving_intent = data["guest"]["moving_intent"]
        self.guest.attaque = data["guest"]["attaque"]

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Une instance de cette fonction est executé pour chaque joueur
        qui se connecte.

        La fonction vérifie que aucun joueur n'est déjà connecté, sinon la
        connexion est refusé.

        Il fait tourner la boucle de communication entre le serveur
        et le joueur"""

        # -- Premier client --
        if not self.connected:
            print("Joueur connecté")
            self.connected = True

            # Arrêt le serveur : n'accepte plus les connections
            self.serveur.close()
            print("N'accepte plus les connexions")

            # Défini les variables à envoyer
            to_send_data = self.get_to_send_data("map")

            writer.write(dict_to_bytes(to_send_data))
            await writer.drain()

            recieved_bytes = await reader.readline()

        # -- Client déjà connecté --
        else:
            writer.close()
            return

        # -- Boucle réseau --
        try:
            while True:

                # -- Si host ferme --
                if self.close:
                    writer.write(dict_to_bytes({"close": True}))
                    await writer.drain()
                    break

                # -- Récupère les données --
                recieved_bytes = await asyncio.wait_for(reader.readline(), timeout=1.0)
                if not recieved_bytes:
                    break

                recieved_data = bytes_to_dict(recieved_bytes)

                # -- Si client ferme --
                if recieved_data["close"]:
                    print("Le client a fermé la connexion")
                    self.close = True
                    break

                # -- Update variables --
                self.update_variables(recieved_data)

                # -- Envoie données --
                to_send_data = self.get_to_send_data()
                to_send_bytes = dict_to_bytes(to_send_data)

                writer.write(to_send_bytes)
                await writer.drain()

                # -- Wait --
                await asyncio.sleep(1 / 30)
        finally:
            # -- Ferme connexion --
            writer.close()
            print("Connexion fermé")

    async def tcp_server(self):
        """Lance le server et donc autorise le client à se connecter."""

        # -- Lancer serveur --
        self.asyncio_loop = asyncio.get_running_loop()
        self.serveur = await asyncio.start_server(
            self.handle_client, host="0.0.0.0", port=8888
        )

        # -- Tourner le serveur --
        print("Attente de client")
        async with self.serveur:
            try:
                await self.serveur.serve_forever()
            except asyncio.CancelledError:
                print("Serveur fermé")

    def stop_server(self):
        """Arrête le protocole de communication avec le client."""

        # -- Définit fonction dtop --
        async def stop_server():
            if self.serveur and self.serveur.is_serving():
                self.serveur.close()
                await self.serveur.wait_closed()

        # -- Appel fonction stop --
        asyncio.run_coroutine_threadsafe(stop_server(), self.asyncio_loop)

    def update(self):
        """Met à jour les éléments nécessaire du joueur et du client."""

        # -- Charge chunks --
        self.map.load_chunks(self.position)

        # -- Update Host --
        self.authority_update(self.guest.hitbox)

        # -- Update Client --
        self.guest.authority_update(self.hitbox)

    def display(self):
        """Affiche le joueur ainsi que l'invité"""

        # -- Client --
        self.guest.display()

        # -- Host --
        super().display()


class GuestController(PlayerControllerBase):
    """Classe pour un client.

    Implémente les joueurs et les fonctions nécessaires ainsi
    que les fonction de communications avec l'hôte."""

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur,
        map: Map,
        address: str,
        port: int,
    ):

        # -- Joueur --
        super().__init__(screen, moteur, map, (0, 0))

        # -- Host --
        self.host = PlayerControllerBase(self.screen, moteur, map, (0, 0))

        # -- Réseau --
        self.address = address
        self.port = port
        self.loaded = False
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        # -- Ennemis --
        self.ennemis_data: Dict[int, Dict[str, Any]]

        # -- Processus --
        self.loop = threading.Thread(target=self.run)
        self.loop.start()

        # -- Interpolation --
        self.target_pos: pygame.Vector2 | None = None
        self.host_target_pos: pygame.Vector2 | None = None

    def set_camera(self, camera: Camera):
        self.camera = camera
        self.host.camera = camera

    def toggle_hitbox(self):
        self.show_hitbox = not self.show_hitbox
        self.host.show_hitbox = self.show_hitbox

    def init_variables(self, data: Dict):
        """Initialise les variables lors de la première connection."""

        # -- Invité --
        self.position.update(data["guest"]["position"])

        # -- Host --
        self.host.moving_intent = data["host"]["moving_intent"]
        self.host.direction = data["host"]["direction"]
        self.host.position.update(data["host"]["position"])

        # -- Map --
        self.map = Map(
            data["map"]["nb_chunks"],
            data["map"]["chunk_size"],
            data["map"]["octaves"],
            (32, 32),
            r"Ressources\Pixel Art Top Down - Basic v1.2.3",
            self.screen,
            data["map"]["seed"],
        )

    async def connect(self):
        """Se connecte au serveur."""

        try:
            # -- Récupère les données --
            self.reader, self.writer = await asyncio.open_connection(
                self.address, self.port
            )

            # Récupère les variables initiales
            recieved_bytes = await self.reader.readline()
            recieved_data = bytes_to_dict(recieved_bytes)
            self.init_variables(recieved_data)

            self.writer.write(dict_to_bytes({"close": False}))

        except ConnectionRefusedError:  # Si pb connexion
            self.close = True

        self.loaded = True

    async def initialize(self):
        """Fonction de lancement du réseau."""

        await self.connect()
        if not self.close:
            await self.handle_host()

    def run(self):
        """Lance le serveur en se connectant à l'hôte puis
        en lancant le processus de communication."""

        asyncio.run(self.initialize())

    def get_to_send_data(self) -> Dict:
        """Créer le dictionnaire de valeurs à envoyer à l'hôte."""
        return {
            "guest": {
                "velocity": list(self.velocity),
                "moving_intent": self.moving_intent,
                "attaque": self.animation.current_state == "attack",
            },
            "close": False,
        }

    def update_variables(self, data: Dict):
        """Update variables."""

        # -- Invité --
        self.target_pos = pygame.Vector2(data["guest"]["position"])
        raw_rect = data["guest"]["attaque_rect"]
        self.attaque_rect = pygame.Rect(raw_rect) if raw_rect else None

        # -- Host --
        self.host_target_pos = pygame.Vector2(data["host"]["position"])
        self.host.moving_intent = data["host"]["moving_intent"]
        self.host.velocity = pygame.Vector2(data["host"]["velocity"])
        self.host.direction = data["host"]["direction"]
        self.host.attaque = data["host"]["attaque"]
        raw_rect = data["host"]["attaque_rect"]
        self.host.attaque_rect = pygame.Rect(raw_rect) if raw_rect else None

        # -- Ennemis --
        self.ennemis_data = data["ennemis"]

    async def handle_host(self):
        """Gére les communications entre le client et l'hôte."""

        try:
            while True:

                # -- Si client ferme --
                if self.close:
                    self.writer.write(dict_to_bytes({"close": True}))
                    await self.writer.drain()
                    break

                # -- Envoie données --
                to_send_data = self.get_to_send_data()
                to_send_bytes = dict_to_bytes(to_send_data)

                self.writer.write(to_send_bytes)
                await self.writer.drain()

                # -- Récupère les donnée --
                recieved_bytes = await asyncio.wait_for(
                    self.reader.readline(), timeout=1.0
                )
                if not recieved_bytes:
                    break

                recieved_data = bytes_to_dict(recieved_bytes)

                # -- Si l'hôte fermé --
                if recieved_data["close"]:
                    self.close = True
                    print("L'hôte a fermé la connexion")
                    break

                self.update_variables(recieved_data)

                # -- Wait --
                await asyncio.sleep(1 / 30)
        finally:
            self.writer.close()
            print("Connexion fermé")

    def update(self):
        """Met à jour les éléments nécessaire du joueur et du client."""

        # -- Map --
        self.map.load_chunks(self.position)

        # -- Guest --
        self.authority_update(self.host.hitbox)

        if self.target_pos is not None:
            delta = (self.target_pos - self.position).length()
            if delta > SPEED * 4:  # téléport si désync > 4 frames de mouvement
                self.position.update(self.target_pos)
            elif delta > SPEED * 0.5:
                lerp = 0.3 if self.moving_intent else 0.6
                self.position += (self.target_pos - self.position) * lerp
            self.hitbox.center = self.position
            self.target_pos = None

        # -- Host --
        self.host.authority_update(self.hitbox)

        if self.host_target_pos is not None:
            delta = (self.host_target_pos - self.host.position).length()
            if delta > SPEED * 1.5:
                self.host.position += (self.host_target_pos - self.host.position) * 0.3
            else:
                self.host.position.update(self.host_target_pos)
            self.host.hitbox.center = self.host.position

    def display(self):
        """Affiche le joueur ainsi que l'hôte"""

        # -- Host --
        self.host.display()

        # -- Guest --
        super().display()

        # -- Debug F2 --
        if self.show_hitbox:
            for obstacle in self.moteur.nearby_obstacles:
                pygame.draw.rect(self.screen, "red", self.camera.apply(obstacle), 2)
