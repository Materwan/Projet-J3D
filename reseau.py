import pygame
import json
import asyncio

pygame.init()


class Controller:

    def __init__(self, screen: pygame.surface.Surface):

        self.screen = screen
        self.running = True
        self.position = [0, 0]
        self.velocity = [0, 0]

    def event(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

        keys = pygame.key.get_pressed()
        self.velocity[0] = int(keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_LEFT]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en x
        self.velocity[1] = int(keys[pygame.K_DOWN]) - int(
            keys[pygame.K_UP]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en y

    def update(self):

        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

    def display_main(self):
        pygame.draw.rect(
            self.screen,
            (255, 0, 255),
            pygame.Rect(
                self.position[0],
                self.position[1],
                10,
                10,
            ),
        )

    def update_screen(self):
        pygame.display.flip()

    def reset_screen(self):
        self.screen.fill((0, 0, 0))


class LocalController(Controller):

    def __init__(self):

        super().__init__()
        self.pressed = False


class NetworkServerController(Controller):

    def __init__(self, screen: pygame.surface.Surface):

        super().__init__(screen)
        self.clients = {}
        self.inputs = {}
        self.outputs = {}

    def event(self):

        super().event()

    async def handle_client(self, reader, writer):

        print(True)
        player_id = id(writer)
        self.clients[player_id] = writer
        self.inputs[player_id] = None
        self.outputs[player_id] = {"state": True, "position": (0, 0)}

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                data = data.decode().strip()
                self.inputs[player_id] = json.loads(data)

                writer.write(bytes(json.dumps(self.outputs[player_id]) + "\n", "utf-8"))
                await writer.drain()
        finally:
            del self.clients[player_id]
            del self.inputs[player_id]
            writer.close()

    async def tcp_server(self):

        server = await asyncio.start_server(
            self.handle_client, host="0.0.0.0", port=8888
        )

        async with server:
            await server.serve_forever()

    def update(self):

        # moteur.moteur()
        super().update()
        for id in self.outputs.keys():
            self.outputs[id] = {"state": True, "position": self.position}

    def display(self):

        super().reset_screen()
        super().display_main()

        for client_id in self.inputs.keys():
            pygame.draw.rect(
                self.screen,
                (255, 0, 255),
                pygame.Rect(
                    self.inputs[client_id]["position"][0],
                    self.inputs[client_id]["position"][1],
                    10,
                    10,
                ),
            )

        super().update_screen()

    async def main(self):

        server_task = asyncio.create_task(self.tcp_server())

        while self.running:

            self.event()
            self.update()
            self.display()

            await asyncio.sleep(1 / 30)

        server_task.cancel()


class NetworkClientController(Controller):

    def __init__(self, screen: pygame.surface.Surface, adresse: str, port: int):

        super().__init__(screen)
        self.pressed = False
        self.adresse = adresse
        self.port = port
        self.data = {"position": (0, 0)}

    async def connect(self):

        self.reader, self.writer = await asyncio.open_connection(
            self.adresse, self.port
        )

    async def event(self):

        super().event()

        await asyncio.sleep(1 / 30)

    async def update(self):

        self.writer.write(
            bytes(json.dumps({"position": self.position}) + "\n", "utf-8")
        )
        await self.writer.drain()

        data = await self.reader.readline()
        data = data.decode().strip()
        data = json.loads(data)
        self.data = data
        super().update()

        await asyncio.sleep(1 / 30)

    async def display(self):

        super().reset_screen()
        super().display_main()

        pygame.draw.rect(
            self.screen,
            (255, 0, 255),
            pygame.Rect(
                self.data["position"][0],
                self.data["position"][1],
                10,
                10,
            ),
        )

        super().update_screen()

        await asyncio.sleep(1 / 30)

    async def main(self):

        await self.connect()

        while self.running:

            await asyncio.gather(self.event(), self.update(), self.display())

        self.writer.close()


screen = pygame.display.set_mode((500, 500))

# asyncio.run(NetworkServerController(screen).main())
asyncio.run(NetworkClientController(screen, "10.90.129.238", 8888).main())

pygame.quit()
