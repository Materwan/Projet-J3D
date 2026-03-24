import pygame
from moteur import Moteur
from map import Map
from camera_system import Camera
from animations import AnimationController, create_player_animation
from typing import Tuple, Dict
import time
import asyncio
import socket
import json
import threading
import psutil

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
        moteur: Moteur,
        map: Map,
        start_position: Tuple[int, int],
    ):
        """Initialise les éléments nécessaires à un joueur"""
        self.screen = screen
        self.camera = None
        self.camera: Camera
        self.moteur = moteur
        self.map = map
        if moteur is not None and map is not None:
            self.moteur.map = map

        self.show_hitbox = False  # pour F2

        # Initialise les animations
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            r"Ressources\Animations\attack",
            (100, 100),
        )
        self.animation = AnimationController(animation_images, self.screen)
        self.im_size = pygame.Vector2(self.animation.im_size)

        # Initialise les données nécessaires pour un joueur
        self.keybinds = None
        self.keybinds: Dict
        self.position = pygame.Vector2(start_position)
        self.hitbox = pygame.Rect(0, 0, 28, 15)
        self.hitbox.center = self.position
        self.velocity = pygame.Vector2(0, 0)
        self.direction = "right"
        self.moving_intent = False

        # attaque
        self.attaque = False
        self.attaque_rect = None

        # reseau
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

    def update(self):
        """Met à jour toutes les données en lien avec le moteur"""

        mov = self.velocity.length_squared()
        if mov > 0:

            if mov > 1:
                self.velocity.normalize_ip()

            self.position += self.velocity * SPEED
            # on cale la hitbox sur le vecteur position
            self.hitbox.center = self.position

    def display(self):
        # La caméra convertit la position en position écran
        screen_pos = pygame.Vector2(self.camera.apply(self.hitbox).center)
        self.animation.display(
            screen_pos - pygame.Vector2(self.im_size[0] // 2, self.im_size[1] - 22)
        )  # -22 pour afficher le joueur un peu au dessus de la hitbox

        if self.show_hitbox:
            pygame.draw.rect(self.screen, "red", self.camera.apply(self.hitbox), 2)
            if self.attaque_rect and self.animation.attacking:
                pygame.draw.rect(
                    self.screen, "red", self.camera.apply(self.attaque_rect), 2
                )


class SoloPlayerController(PlayerControllerBase):
    """Classe pour un joueur solo"""

    def __init__(
        self,
        screen: pygame.Surface,
        moteur: Moteur,
        map: Map,
        start_position: Tuple[int, int],
    ):
        super().__init__(screen, moteur, map, start_position)

    def set_camera(self, camera):
        self.camera = camera

    def toggle_hitbox(self):
        self.show_hitbox = not self.show_hitbox

    def event(self, keys):

        super().event(keys)

    def update(self):

        self.map.load_chunks(self.position)

        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:  # si le joueur veut se deplacer alors :

            self.update_direction()

            self.moteur.collision(self.hitbox, self.velocity, None)

            super().update()

        if self.attaque:
            self.animation.trigger_attack()
            self.attaque_rect = self.moteur.create_rect_attaque(
                self.position, self.direction
            )
            self.attaque = False  # consommé, on attend le prochain appui

        self.animation.update(self.moving_intent, self.direction)

    def display(self):

        super().display()

        if self.show_hitbox:
            for obstacle in self.moteur.nearby_obstacles:
                pygame.draw.rect(self.screen, "red", self.camera.apply(obstacle), 2)


class HostController(PlayerControllerBase):
    """Classe pour un hôte de partie.\n
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

        super().__init__(screen, moteur, map, start_position)

        # Initialise les données de l'invité
        self.guest = PlayerControllerBase(
            self.screen, moteur, self.map, (start_position[0] + 50, start_position[1])
        )

        self.serveur: asyncio.Server  # pour savoir le type
        self.serveur = None  # initialise
        self.connected = False  # True si un invité est connecté

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

    def set_camera(self, camera):
        self.camera = camera
        self.guest.camera = camera

    def toggle_hitbox(self):
        self.show_hitbox = not self.show_hitbox
        self.guest.show_hitbox = self.show_hitbox

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
            json.dumps({"Game name": "My game", "Port": 8888, "last": time.time()})
            + "\n",
            encoding="utf-8",
        )  # définit le message à envoyer

        while self.udp_run:  # tourne tant que le serveur n'es pas fermé
            try:
                sock.sendto(message, (broadcast_ip, UDP_PORT))
            except socket.timeout:
                pass
            if self.connected or self.close:
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
                    "attaque_rect": (
                        list(self.guest.attaque_rect)
                        if self.guest.attaque_rect and self.guest.animation.attacking
                        else None
                    ),
                },
                "host": {
                    "position": list(self.position),
                    "moving_intent": self.moving_intent,
                    "direction": self.direction,
                    "attaque": self.attaque,
                    "attaque_rect": (
                        list(self.attaque_rect)
                        if self.attaque_rect and self.animation.attacking
                        else None
                    ),  # attaque_rect sert juste pour l'affichage de la hitbox d'attaque si F2 enclencher
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
        print("N'accepte plus les connexions")

        # Défini les variables à envoyer
        to_send_data = get_to_send_data()
        to_send_data["map"] = {
            "nb_chunks": self.map.nb_chunks.tolist(),
            "chunk_size": self.map.chunk_size_tile.tolist(),
            "octaves": self.map.octaves,
            "seed": self.map.seed,
        }
        writer.write(dict_to_bytes(to_send_data))
        await writer.drain()

        recieved_bytes = await reader.readline()

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

                # Met à jour les variables
                self.guest.velocity = self.moteur.verif_velocity(
                    recieved_data["guest"]["velocity"]
                )  # verification de la vélocité dès qu'on le recoit
                self.guest.moving_intent = recieved_data["guest"]["moving_intent"]
                self.guest.attaque = recieved_data["guest"]["attaque"]

                # Défini les variables à envoyer et les encodes
                to_send_data = get_to_send_data()
                # dès qu'on envoie attaque = True une fois au client on met sur False
                self.attaque = False
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
        """Arrête le protocole de communication avec le client."""

        async def stop_server():
            if self.serveur and self.serveur.is_serving():
                self.serveur.close()
                await self.serveur.wait_closed()

        asyncio.run_coroutine_threadsafe(stop_server(), self.asyncio_loop)

    def event(self, keys):

        super().event(keys)

    def update(self):

        self.map.load_chunks(self.position)

        # Hôte
        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:  # Si l'hôte veux bouger

            self.update_direction()

            self.moteur.collision(self.hitbox, self.velocity, self.guest.hitbox)

            super().update()

        if self.attaque and not self.connected:
            self.animation.trigger_attack()
            self.attaque_rect = self.moteur.create_rect_attaque(
                self.position, self.direction
            )
            self.attaque = False

        elif self.attaque:
            self.animation.trigger_attack()
            self.attaque_rect = self.moteur.create_rect_attaque(
                self.position, self.direction
            )
            # le self.attaque = False de l'hôte est effectuer juste après l'avoir envoyer au client

        self.animation.update(self.moving_intent, self.direction)

        # Client
        if self.guest.moving_intent:  # Si le client veux bouger

            self.guest.update_direction()

            self.moteur.collision(self.guest.hitbox, self.guest.velocity, self.hitbox)

            self.guest.update()

        if self.guest.attaque:  # regarde si client attaque
            self.guest.animation.trigger_attack()
            self.guest.attaque_rect = self.moteur.create_rect_attaque(
                self.guest.position, self.guest.direction
            )
            self.guest.attaque = False

        self.guest.animation.update(self.guest.moving_intent, self.guest.direction)

    def display(self):
        """Affiche le joueur ainsi que l'invité"""

        self.guest.display()

        super().display()

        if self.show_hitbox:
            for obstacle in self.moteur.nearby_obstacles:
                pygame.draw.rect(self.screen, "red", self.camera.apply(obstacle), 2)


class GuestController(PlayerControllerBase):
    """Classe pour un client.\n
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

        super().__init__(screen, moteur, map, (0, 0))
        # Défini un player pour l'hôte
        self.host = PlayerControllerBase(self.screen, None, map, (0, 0))

        self.address = address
        self.port = port
        self.loaded = False

        # Défini un processus pour la connexion
        # sur un autre thread du processeur
        self.loop = threading.Thread(target=self.run)
        self.loop.start()

        # position du client et l'hôte reçu par le serveur/hôte
        self.server_pos = None
        self.host_target_pos = None

    def set_camera(self, camera):
        self.camera: Camera
        self.camera = camera
        self.host.camera = camera

    def toggle_hitbox(self):
        self.show_hitbox = not self.show_hitbox
        self.host.show_hitbox = self.show_hitbox

    async def connect(self):
        """Se connecte au serveur"""

        try:
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

            self.map = Map(
                recieved_data["map"]["nb_chunks"],
                recieved_data["map"]["chunk_size"],
                recieved_data["map"]["octaves"],
                (32, 32),
                r"Ressources\Pixel Art Top Down - Basic v1.2.3",
                self.screen,
                recieved_data["map"]["seed"],
            )

            self.writer.write(dict_to_bytes({"close": False}))
        except ConnectionRefusedError:
            self.close = True

        self.loaded = True

    async def initialize(self):
        """Fonction de lancement du réseau"""

        await self.connect()
        if not self.close:
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
                    "attaque": self.attaque,
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
                self.attaque = False  # consommé après envoi
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
                self.server_pos = pygame.Vector2(recieved_data["guest"]["position"])
                raw_rect = recieved_data["guest"]["attaque_rect"]
                self.attaque_rect = pygame.Rect(raw_rect) if raw_rect else None

                self.host_target_pos = pygame.Vector2(recieved_data["host"]["position"])
                self.host.moving_intent = recieved_data["host"]["moving_intent"]
                self.host.direction = recieved_data["host"]["direction"]
                self.host.attaque = recieved_data["host"]["attaque"]
                raw_rect = recieved_data["host"]["attaque_rect"]
                self.host.attaque_rect = pygame.Rect(raw_rect) if raw_rect else None

                # Attend de manière à ce qu'il y ai 30 envoie par secondes
                await asyncio.sleep(1 / 30)
        finally:
            self.writer.close()
            print("Connexion fermé")

    def event(self, keys):

        super().event(keys)

    def update(self):

        self.map.load_chunks(self.position)

        # le client calcule de son côté ça propre direction et moving_intent
        # + Client Side prediction : bouge sans attendre le serveur
        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:
            self.update_direction()
            self.moteur.collision(self.hitbox, self.velocity, self.host.hitbox)
            super().update()

        # mise à jour fluide de la position du client : corrige doucement l'écart
        if self.server_pos is not None:
            delta = (self.server_pos - self.position).length()
            if delta > SPEED * 4:  # téléport si désync > 4 frames de mouvement
                self.position.update(self.server_pos)
            elif delta > SPEED * 0.5:
                lerp = 0.3 if self.moving_intent else 0.6
                self.position += (self.server_pos - self.position) * lerp
            self.hitbox.center = self.position
            self.server_pos = None

        if self.host_target_pos is not None:
            delta = (self.host_target_pos - self.host.position).length()
            if delta > SPEED * 1.5:
                self.host.position += (self.host_target_pos - self.host.position) * 0.3
            else:
                self.host.position.update(self.host_target_pos)
            self.host.hitbox.center = self.host.position

        # gestion animation attaque
        if self.attaque:
            self.animation.trigger_attack()
            # le self.attaque = False du client est effectuer juste après l'avoir envoyer a l'hôte

        if self.host.attaque:
            self.host.animation.trigger_attack()
            self.host.attaque = False

        # gestion animation
        self.animation.update(self.moving_intent, self.direction)
        self.host.animation.update(self.host.moving_intent, self.host.direction)

    def display(self):
        """Affiche le joueur ainsi que l'hôte"""

        self.host.display()

        super().display()

        if self.show_hitbox:
            for obstacle in self.moteur.nearby_obstacles:
                pygame.draw.rect(self.screen, "red", self.camera.apply(obstacle), 2)
