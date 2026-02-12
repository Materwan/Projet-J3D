import pygame
from moteur import Moteur
from animations import AnimationController, create_player_animation
from typing import Tuple, Dict
import asyncio
import json
import threading


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

    """def update(self):

        moving_intent = self.velocity.length_squared() > 0
        if moving_intent:  # si le joueur veut se deplacer alors :

            # gestion collision
            self.moteur.collision(self.hitbox, self.velocity, None)

            is_moving = self.velocity.length_squared()
            if is_moving > 0:  # si on se deplace toujours alors :

                # gestion des déplacements en diagonales
                if is_moving > 1:  # si deplacement en diagonale
                    self.velocity.normalize_ip()  # [1, 1] devient [0.707107, 0.707107]

                # gestion du vecteur position
                self.position += self.velocity * 2
                # la position de la hitbox se cale sur le vecteur position
                self.hitbox.topleft = self.position

                # gestion de la direction /// en attente de animation up et down
                if self.velocity.x < 0:
                    self.direction = "left"
                elif self.velocity.x > 0:
                    self.direction = "right"

        self.animation.update(moving_intent, self.direction)"""

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

        self.loop = threading.Thread(target=self.initialize)
        self.loop.start()
        """self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.tcp_server())
        self.loop.run_forever()"""
        # asyncio.run(self.initialize())

    def initialize(self):

        self.serveur_task = asyncio.run(self.tcp_server())

    def event(self, keys: Tuple[bool]):

        super().event(keys)

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):

        # Si un au client est connecté
        if self.connected:
            writer.close()
            await writer.wait_closed()
            return

        # Si aucun autre client n'est connecté
        print("Joueur connecté")
        self.connected = True

        # Arrêt le serveur : n'accepte plus les connections
        self.serveur.close()
        # await self.serveur.wait_closed()
        print("Serveur fermé")

        # Gestion du client
        player_id = id(writer)
        self.writter = writer

        try:
            while True:
                # print("aaaaaaaaaaaaaaaaaaaaaaaaa")
                recieved_bytes = await reader.readline()
                if not recieved_bytes:
                    break
                # print("psjngonsdcovjn")
                recieved_str = recieved_bytes.decode().strip()
                recieved_data = json.loads(recieved_str)
                # print(recieved_data)
                self.guest.velocity.update(recieved_data["guest"]["velocity"])
                self.guest.moving_intent = recieved_data["guest"]["moving_intent"]
                self.guest.direction = recieved_data["guest"]["direction"]

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
                }
                to_send_bytes = bytes(json.dumps(to_send_data) + "\n", "utf-8")

                writer.write(to_send_bytes)
                await writer.drain()

                await asyncio.sleep(1 / 30)
        finally:
            writer.close()

    async def tcp_server(self):

        self.serveur = await asyncio.start_server(
            self.handle_client, host="0.0.0.0", port=8888
        )

        print("Attente de client")
        async with self.serveur:
            await self.serveur.serve_forever()

    def update(self):

        self.moving_intent = self.velocity.length_squared() > 0
        # print(self.moving_intent)
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
                to_send_data = {
                    "guest": {
                        "velocity": list(self.velocity),
                        "moving_intent": self.moving_intent,
                        "direction": self.direction,
                    }
                }
                # print(True)
                to_send_bytes = bytes(json.dumps(to_send_data) + "\n", "utf-8")
                #print("writer:", self.writer)
                #print("socket:", self.writer.get_extra_info("socket"))
                #print(to_send_data)
                #print(to_send_bytes)
                self.writer.write(to_send_bytes)
                await self.writer.drain()

                recieved_bytes = await self.reader.readline()
                if not recieved_bytes:
                    break
                recieved_str = recieved_bytes.decode().strip()
                recieved_data = json.loads(recieved_str)

                # Update variables
                #print("Guest position : ", recieved_data["guest"]["position"])
                #print("Guest velocity : ", recieved_data["guest"]["velocity"])
                # print("Host position : ", recieved_data["host"]["position"])
                #print("Host moving intent : ", recieved_data["host"]["moving_intent"])
                #print("Host direction : ", recieved_data["host"]["direction"])
                self.position.update(recieved_data["guest"]["position"])
                self.velocity.update(recieved_data["guest"]["velocity"])
                self.host.position.update(recieved_data["host"]["position"])
                #print(recieved_data["host"]["moving_intent"])
                self.host.moving_intent = recieved_data["host"]["moving_intent"]
                self.host.direction = recieved_data["host"]["direction"]

                await asyncio.sleep(1 / 30)
        finally:
            pass

    def update(self):

        #print(self.host.moving_intent)
        self.moving_intent = self.velocity.length_squared() > 0
        if self.moving_intent:

            self.look_direction = self.velocity.normalize()

            super().update()
        
        if self.host.moving_intent:

            # print("moving intent")
            self.host.update()
            self.host.hitbox.topleft = self.host.position

        print("Host position : ", self.host.hitbox.topleft)
        self.animation.update(self.moving_intent, self.direction)
        self.host.animation.update(self.host.moving_intent, self.host.direction)

    def display(self):
        """Affiche le joueur ainsi que l'hôte"""

        super().display()
        self.host.display()
