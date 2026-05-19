"""Module réseau : HostNetwork et GuestNetwork."""

import asyncio
import socket
import threading
import time
import json
import psutil
from collections import deque
from typing import Dict, Any, Optional

# Configuration des ports
UDP_PORT = 9999  # (découverte de parties)
TCP_PORT = 8888  # (le jeu)
NETWORK_TICK = 1 / 60  # tick du réseau

RTT_WINDOW = 60  # nombre de mesures conservées pour le calcul de la moyenne


def get_netmask_for_ip(ip: str) -> Optional[str]:
    """Récupère le masque de sous-réseau pour une IP donnée."""
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == ip:
                return addr.netmask
    return None


def get_broadcast_ip(ip: str, subnet_mask: str) -> str:
    """Calcule l'adresse de broadcast à partir de l'IP et du masque."""
    parts = []
    for ip_byte, mask_byte in zip(ip.split("."), subnet_mask.split(".")):
        parts.append(ip_byte if mask_byte == "255" else "255")
    return ".".join(parts)


def dict_to_bytes(data: Dict) -> bytes:
    """Transforme un dictionnaire en octets pour l'envoi."""
    return bytes(json.dumps(data) + "\n", "utf-8")


def bytes_to_dict(data: bytes) -> Optional[Dict]:
    """Décode les octets reçus en dictionnaire."""
    if not data:
        return None
    return json.loads(data.decode().strip())


class RttTracker:
    """
    Calcule le RTT moyen sur une fenêtre glissante de mesures.

    Utilisation :
        tracker = RttTracker(window=60)
        t0 = tracker.start()          # juste avant l'envoi
        ...reception de la réponse...
        tracker.record(t0)            # enregistre la mesure
        print(tracker.average_ms)     # RTT moyen en millisecondes
    """

    def __init__(self, window: int = RTT_WINDOW):
        self._samples: deque[float] = deque(maxlen=window)
        self._lock = threading.Lock()

    def start(self) -> float:
        """Retourne le timestamp actuel à passer à record()."""
        return time.perf_counter()

    def record(self, t0: float) -> float:
        """Enregistre une mesure RTT (en ms) et la retourne."""
        rtt_ms = (time.perf_counter() - t0) * 1000.0
        with self._lock:
            self._samples.append(rtt_ms)
        return rtt_ms

    @property
    def average_ms(self) -> float:
        """RTT moyen en millisecondes sur la fenêtre courante. 0.0 si aucune mesure."""
        with self._lock:
            if not self._samples:
                return 0.0
            return sum(self._samples) / len(self._samples)

    @property
    def last_ms(self) -> float:
        """Dernier RTT mesuré en millisecondes. 0.0 si aucune mesure."""
        with self._lock:
            return self._samples[-1] if self._samples else 0.0

    @property
    def sample_count(self) -> int:
        """Nombre de mesures actuellement dans la fenêtre."""
        with self._lock:
            return len(self._samples)


class HostNetwork:
    """
    Côté Host : serveur TCP + broadcast UDP.

    Deux threads dédiés, indépendants du game loop :
        - _tcp_thread  : asyncio server, accepte 1 client max
        - _udp_thread  : broadcast UDP jusqu'à connexion du client
    """

    def __init__(self, port: int = TCP_PORT):
        self.port = port
        self.ip = socket.gethostbyname(socket.gethostname())
        self.subnet_mask = get_netmask_for_ip(self.ip)

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._connected = False
        self._guest_disconnected = False

        self._outgoing_back: Dict[str, Any] = {}
        self._outgoing_front: Dict[str, Any] = {}
        self._outgoing_dirty = False

        self._incoming_back: Dict[str, Any] = {}
        self._incoming_front: Dict[str, Any] = {}
        self._incoming_dirty = False

        self._initial_state: Optional[Dict[str, Any]] = None

        self._server: Optional[asyncio.Server] = None
        self._asyncio_loop: Optional[asyncio.AbstractEventLoop] = None

        self._tcp_thread = threading.Thread(target=self._run_tcp, daemon=True)
        self._udp_thread = threading.Thread(target=self._run_udp, daemon=True)

        # RTT : le host reçoit le rtt_ms moyen mesuré par le guest dans chaque paquet
        self._guest_rtt_ms: float = 0.0

    def start(self, initial_state: Optional[Dict[str, Any]] = None):
        """Lance TCP + UDP. initial_state doit contenir les données de map."""
        if initial_state is not None:
            with self._lock:
                self._outgoing_back = initial_state
                self._outgoing_dirty = True
                self._initial_state = initial_state
        self._tcp_thread.start()
        self._udp_thread.start()

    def close(self):
        """Signale l'arrêt propre des threads réseau."""
        self._stop_event.set()
        if (
            self._asyncio_loop is not None
            and not self._asyncio_loop.is_closed()
            and self._server is not None
        ):
            self._asyncio_loop.call_soon_threadsafe(self._server.close)

    def restart_listening(self):
        """Remet le serveur en écoute après déconnexion du guest."""
        self._guest_disconnected = False
        self._connected = False
        self._server = None
        self._asyncio_loop = None
        self._guest_rtt_ms = 0.0

        with self._lock:
            self._outgoing_back = {}
            self._outgoing_front = {}
            self._outgoing_dirty = False
            self._incoming_back = {}
            self._incoming_front = {}
            self._incoming_dirty = False

        self._tcp_thread = threading.Thread(target=self._run_tcp, daemon=True)
        self._udp_thread = threading.Thread(target=self._run_udp, daemon=True)
        self._tcp_thread.start()
        self._udp_thread.start()

    def is_guest_disconnected(self) -> bool:
        """True si c'est le guest qui s'est déconnecté (pas un arrêt volontaire du host)."""
        return self._guest_disconnected and not self._stop_event.is_set()

    def is_connected(self) -> bool:
        return self._connected and not self._stop_event.is_set()

    def is_closed(self) -> bool:
        return self._stop_event.is_set()

    @property
    def guest_rtt_ms(self) -> float:
        """RTT moyen du guest (en ms), tel que rapporté par le guest lui-même."""
        return self._guest_rtt_ms

    def update(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Appelé par le game loop à 60 FPS — O(1), juste un swap de référence."""
        with self._lock:
            self._outgoing_back = game_state
            self._outgoing_dirty = True

            if self._incoming_dirty:
                self._incoming_front, self._incoming_back = (
                    self._incoming_back,
                    self._incoming_front,
                )
                self._incoming_dirty = False

                # Récupère le RTT moyen rapporté par le guest
                rtt = self._incoming_front.get("rtt_ms")
                if rtt is not None:
                    self._guest_rtt_ms = rtt

                return self._incoming_front

            return {}

    def _get_outgoing(self) -> Dict[str, Any]:
        with self._lock:
            if self._outgoing_dirty:
                self._outgoing_front, self._outgoing_back = (
                    self._outgoing_back,
                    self._outgoing_front,
                )
                self._outgoing_dirty = False
            return self._outgoing_front

    def _set_incoming(self, data: Dict[str, Any]):
        with self._lock:
            self._incoming_back = data
            self._incoming_dirty = True

    # ── TCP ───────────────────────────────────────────────────────────────────

    def _run_tcp(self):
        asyncio.run(self._tcp_server())

    async def _tcp_server(self):
        self._asyncio_loop = asyncio.get_running_loop()
        self._server = await asyncio.start_server(
            self._handle_client,
            host="0.0.0.0",
            port=self.port,
            reuse_address=True,
        )
        print(f"[Host] Serveur TCP démarré — port {self.port}")
        async with self._server:
            try:
                await self._server.serve_forever()
            except asyncio.CancelledError:
                print("[Host] Serveur TCP fermé")

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        if self._connected:
            writer.close()
            return

        print("[Host] Guest connecté")
        self._connected = True

        # Envoi initial : état courant (contient la map)
        writer.write(dict_to_bytes(self._initial_state))
        await writer.drain()

        # ACK du guest
        await reader.readline()

        try:
            while not self._stop_event.is_set():
                raw = await asyncio.wait_for(reader.readline(), timeout=2.0)
                if not raw:
                    print(
                        "[Host] Le Guest s'est déconnecté (probablement car l'Host a freeze, provoquant un timeout chez le Guest)"
                    )
                    self._guest_disconnected = True
                    break

                data = bytes_to_dict(raw)
                if data is None or data.get("close"):
                    print("[Host] Guest a fermé la connexion")
                    self._guest_disconnected = True
                    break

                self._set_incoming(data)

                writer.write(dict_to_bytes(self._get_outgoing()))
                await writer.drain()

        except asyncio.TimeoutError:
            print("[Host] Timeout — guest injoignable")
            self._guest_disconnected = True
        except ConnectionResetError:
            print("[Host] Connexion réinitialisée par le guest")
            self._guest_disconnected = True
        finally:
            writer.close()
            self._connected = False
            print("[Host] Connexion fermée")
            if self._server is not None:
                self._server.close()

    # ── UDP ───────────────────────────────────────────────────────────────────

    def _run_udp(self):
        if self.subnet_mask is None:
            print("[Host] Masque réseau introuvable — broadcast UDP désactivé")
            return

        broadcast_ip = get_broadcast_ip(self.ip, self.subnet_mask)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.5)

        message = dict_to_bytes(
            {"Game name": "MoleTale", "Port": self.port, "last": time.time()}
        )

        print(f"[Host] Broadcast UDP → {broadcast_ip}:{UDP_PORT}")

        while not self._stop_event.is_set() and not self._connected:
            try:
                sock.sendto(message, (broadcast_ip, UDP_PORT))
            except socket.timeout:
                pass
            time.sleep(0.5)

        sock.close()
        print("[Host] Broadcast UDP arrêté")


class GuestNetwork:
    """
    Côté guest : client TCP.

    Un seul thread dédié, indépendant du game loop.
    Appeler is_loaded() pour savoir si la tentative de connexion est terminée.
    Appeler get_map_data() pour récupérer les données de map reçues à la connexion.

    Le RTT est calculé à chaque échange : on horodate l'envoi et on mesure
    le délai jusqu'à la réception de la réponse. La moyenne glissante est
    accessible via rtt_tracker.average_ms (ou rtt_ms pour la dernière valeur).
    La valeur moyenne est également injectée dans chaque paquet envoyé
    (clé "rtt_ms") afin que le host puisse la consulter.
    """

    def __init__(self, address: str, port: int = TCP_PORT):
        self.address = address
        self.port = port

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._connected = False
        self._loaded = False

        self._outgoing_back: Dict[str, Any] = {}
        self._outgoing_front: Dict[str, Any] = {}
        self._outgoing_dirty = False

        self._incoming_back: Dict[str, Any] = {}
        self._incoming_front: Dict[str, Any] = {}
        self._incoming_dirty = False

        self._map_data: Optional[Dict[str, Any]] = None

        self._tcp_thread = threading.Thread(target=self._run, daemon=True)
        self._close_sent = threading.Event()

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

        # RTT
        self.rtt_tracker = RttTracker(window=RTT_WINDOW)

    # ── Propriétés RTT ────────────────────────────────────────────────────────

    @property
    def rtt_ms(self) -> float:
        """Dernier RTT mesuré en millisecondes."""
        return self.rtt_tracker.last_ms

    @property
    def average_rtt_ms(self) -> float:
        """RTT moyen en millisecondes sur la fenêtre glissante."""
        return self.rtt_tracker.average_ms

    # ── Interface publique ────────────────────────────────────────────────────

    def start(self, initial_state: Optional[Dict[str, Any]] = None):
        """Lance la connexion TCP. initial_state ignoré côté guest."""
        self._tcp_thread.start()

    def close(self):
        """Signale l'arrêt propre du thread réseau."""
        self._stop_event.set()

    def is_connected(self) -> bool:
        return self._connected and not self._stop_event.is_set()

    def is_closed(self) -> bool:
        return self._stop_event.is_set()

    def is_loaded(self) -> bool:
        """True quand la tentative de connexion est terminée (succès ou échec)."""
        return self._loaded

    def get_map_data(self) -> Optional[Dict[str, Any]]:
        """Retourne les données de map reçues à la connexion initiale."""
        return self._map_data

    def update(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Appelé par le game loop à 60 FPS — O(1), juste un swap de référence."""
        with self._lock:
            # Injecte le RTT moyen courant dans le paquet sortant
            game_state["rtt_ms"] = self.rtt_tracker.average_ms

            self._outgoing_back = game_state
            self._outgoing_dirty = True

            if self._incoming_dirty:
                self._incoming_front, self._incoming_back = (
                    self._incoming_back,
                    self._incoming_front,
                )
                self._incoming_dirty = False
                return self._incoming_front

            return {}

    def _get_outgoing(self) -> Dict[str, Any]:
        with self._lock:
            if self._outgoing_dirty:
                self._outgoing_front, self._outgoing_back = (
                    self._outgoing_back,
                    self._outgoing_front,
                )
                self._outgoing_dirty = False
            return self._outgoing_front

    def _set_incoming(self, data: Dict[str, Any]):
        with self._lock:
            self._incoming_back = data
            self._incoming_dirty = True

    def get_initial_state(self) -> Dict[str, Any]:
        """Retourne le premier paquet reçu (état initial + map)."""
        with self._lock:
            return dict(self._incoming_back)

    def request_close(self):
        """Demande l'envoi d'un paquet close puis coupe la connexion."""
        with self._lock:
            self._outgoing_back = {"close": True}
            self._outgoing_dirty = True
        self._close_sent.wait(timeout=0.5)
        self.close()

    # ── TCP ───────────────────────────────────────────────────────────────────

    def _run(self):
        asyncio.run(self._initialize())

    async def _initialize(self):
        await self._connect()
        if not self._stop_event.is_set():
            await self._handle_host()

    async def _connect(self):
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.address, self.port
            )

            # Réception du premier paquet (contient la map + état initial)
            raw = await self._reader.readline()
            data = bytes_to_dict(raw)
            if data is None or data.get("close"):
                self._stop_event.set()
                return

            self._map_data = data["map"]
            self._set_incoming(data)

            # ACK
            self._writer.write(dict_to_bytes({"close": False}))
            await self._writer.drain()

            self._connected = True
            print(f"[Guest] Connecté à {self.address}:{self.port}")

        except ConnectionRefusedError:
            print(f"[Guest] Connexion refusée — {self.address}:{self.port}")
            self._stop_event.set()
        except OSError as e:
            print(f"[Guest] Erreur réseau : {e}")
            self._stop_event.set()
        finally:
            self._loaded = True  # Toujours signaler que la tentative est terminée

    async def _handle_host(self):
        try:
            while not self._stop_event.is_set():
                snapshot = self._get_outgoing()
                self._writer.write(dict_to_bytes(snapshot))
                await self._writer.drain()
                if snapshot.get("close"):
                    self._close_sent.set()

                # Horodatage juste avant l'attente de la réponse
                t0 = self.rtt_tracker.start()

                raw = await asyncio.wait_for(self._reader.readline(), timeout=2.0)
                if not raw:
                    print("[Guest] Host a fermé la connexion")
                    self._stop_event.set()
                    break

                # Enregistrement du RTT dès la réception
                self.rtt_tracker.record(t0)

                data = bytes_to_dict(raw)
                if data is None or data.get("close"):
                    print("[Guest] Host a fermé la connexion")
                    self._stop_event.set()
                    break

                self._set_incoming(data)

                await asyncio.sleep(NETWORK_TICK)

        except asyncio.TimeoutError:
            print("[Guest] Timeout — Host injoignable")
            self._stop_event.set()
        except ConnectionResetError:
            print("[Guest] Connexion réinitialisée par l'Host")
            self._stop_event.set()
        finally:
            self._writer.close()
            self._connected = False
            print("[Guest] Connexion fermée")
