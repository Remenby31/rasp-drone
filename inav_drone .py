import serial
import struct
import threading
import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple


# ===================== Métriques =====================

@dataclass
class Attitude:
    roll: float = 0.0   # degrés
    pitch: float = 0.0  # degrés
    yaw: float = 0.0    # degrés

@dataclass
class GPSState:
    lat: Optional[float] = None   # degrés
    lon: Optional[float] = None   # degrés
    alt: Optional[float] = None   # m
    speed: float = 0.0            # m/s
    ground_course: float = 0.0    # degrés
    hdop: float = 0.0             # HDOP
    sats: int = 0
    fix_type: int = 0             # 0=no fix, 2=2D, 3=3D...

@dataclass
class AltitudeState:
    estimated_alt: float = 0.0    # m (altitude estimée par le FC)
    vario: float = 0.0            # cm/s (variomètre - taux de montée/descente)

@dataclass
class BatteryState:
    voltage: float = 0.0    # V
    mah: float = 0.0        # mAh consommés (approx)

@dataclass
class NavStatus:
    mode: str = "UNKNOWN"   # notre vue “logique” (ANGLE / NAV_WP / POSHOLD / RTH...)
    # tu peux ajouter d’autres champs si tu décodes MSP_NAV_STATUS


# ===================== Classe principale =====================

class INavDrone:
    """
    Contrôle d'un drone iNAV via MSP v1.

    - Connexion série / MSP
    - Télémétrie : attitude, GPS, batterie, RC
    - Contrôle RC (MSP_SET_RAW_RC)
    - Navigation basique : go_to, follow_path, climb_to
    """

    # Command IDs MSP
    MSP_RC         = 105
    MSP_RAW_GPS    = 106
    MSP_ATTITUDE   = 108
    MSP_ALTITUDE   = 109
    MSP_ANALOG     = 110
    MSP_NAV_STATUS = 121  # non utilisé pour l’instant

    MSP_SET_RAW_RC = 200
    MSP_SET_WP     = 209

    def __init__(self, port: str, baudrate: int = 115200, poll_interval: float = 0.1, rc_update_hz: float = 20.0):
        self.port = port
        self.baudrate = baudrate
        self.poll_interval = poll_interval
        self.rc_update_interval = 1.0 / rc_update_hz  # Intervalle pour MSP_SET_RAW_RC (min 5Hz requis)

        self._ser: Optional[serial.Serial] = None
        self._running = False
        self._poll_thread: Optional[threading.Thread] = None
        self._rc_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()  # pour protéger le port série

        # Métriques
        self.attitude = Attitude()
        self.gps = GPSState()
        self.altitude = AltitudeState()
        self.battery = BatteryState()
        self.nav = NavStatus()
        self.armed: bool = False

        # RC (1000–2000 µs)
        self.rc_channels: Dict[int, int] = {i: 1500 for i in range(1, 9)}  # 8 canaux par défaut
        self._rc_override_enabled = False  # Active la transmission continue MSP_SET_RAW_RC

    # ------------- Connexion / boucle de télémétrie -------------

    def connect(self):
        """Ouvre le port MSP et lance les boucles de télémétrie et RC."""
        self._ser = serial.Serial(self.port, self.baudrate, timeout=0.2)
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        self._rc_thread = threading.Thread(target=self._rc_loop, daemon=True)
        self._rc_thread.start()

    def disconnect(self):
        """Arrête les boucles et ferme le port série."""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=1.0)
        if self._rc_thread:
            self._rc_thread.join(timeout=1.0)
        if self._ser:
            self._ser.close()
            self._ser = None

    def _poll_loop(self):
        while self._running:
            try:
                self._update_metrics_once()
            except Exception as e:
                print("[INavDrone] Poll error:", e)
            time.sleep(self.poll_interval)

    def _rc_loop(self):
        """
        Boucle de transmission continue des canaux RC via MSP_SET_RAW_RC.
        IMPORTANT: iNav requiert MSP_SET_RAW_RC à ≥5Hz pour éviter le failsafe RC.
        """
        while self._running:
            try:
                if self._rc_override_enabled:
                    self._send_rc_channels()
            except Exception as e:
                print("[INavDrone] RC loop error:", e)
            time.sleep(self.rc_update_interval)

    def _update_metrics_once(self):
        """Lit une fois chaque télémétrie principale via MSP (bloquant court)."""
        # ATTITUDE
        try:
            payload = self._msp_request(self.MSP_ATTITUDE)
            if payload and len(payload) >= 6:
                angx, angy, heading = struct.unpack('<hhh', payload[:6])
                self.attitude.roll = angx / 10.0
                self.attitude.pitch = angy / 10.0
                self.attitude.yaw = heading / 10.0  # deci-degrees to degrees
        except Exception as e:
            print("[INavDrone] ATTITUDE error:", e)

        # RAW_GPS
        try:
            payload = self._msp_request(self.MSP_RAW_GPS)
            if payload and len(payload) >= 18:
                fix, sats, lat_i, lon_i, alt_cm, speed_cms, gc_decdeg, hdop = struct.unpack('<BBllhhhH', payload[:18])
                self.gps.fix_type = fix
                self.gps.sats = sats
                self.gps.lat = lat_i / 1e7
                self.gps.lon = lon_i / 1e7
                self.gps.alt = alt_cm / 100.0           # cm to m
                self.gps.speed = speed_cms / 100.0      # cm/s to m/s
                self.gps.ground_course = gc_decdeg / 10.0  # deci-degrees to degrees
                self.gps.hdop = hdop / 100.0            # HDOP
        except Exception as e:
            print("[INavDrone] RAW_GPS error:", e)

        # ALTITUDE
        try:
            payload = self._msp_request(self.MSP_ALTITUDE)
            if payload and len(payload) >= 6:
                alt_cm, vario_cms = struct.unpack('<lh', payload[:6])
                self.altitude.estimated_alt = alt_cm / 100.0  # cm to m
                self.altitude.vario = float(vario_cms)        # cm/s
        except Exception as e:
            print("[INavDrone] ALTITUDE error:", e)

        # ANALOG (bat)
        try:
            payload = self._msp_request(self.MSP_ANALOG)
            if payload and len(payload) >= 7:
                vbat_raw = payload[0]          # 0.1V units
                mah_drawn, rssi, amps = struct.unpack('<HHH', payload[1:7])
                self.battery.voltage = vbat_raw / 10.0
                self.battery.mah = float(mah_drawn)
        except Exception as e:
            print("[INavDrone] ANALOG error:", e)

        # RC
        try:
            payload = self._msp_request(self.MSP_RC)
            if payload and len(payload) >= 16:
                n_ch = len(payload) // 2
                values = struct.unpack('<' + 'H' * n_ch, payload)
                for i, v in enumerate(values, start=1):
                    self.rc_channels[i] = v
        except Exception as e:
            print("[INavDrone] RC error:", e)

    # ------------- MSP bas niveau -------------

    def _msp_send(self, cmd: int, payload: bytes = b''):
        """Envoie un paquet MSP v1 (-> FC)."""
        if not self._ser:
            raise RuntimeError("Port série non ouvert")

        length = len(payload)
        header = b'$M>'
        body = bytes([length, cmd]) + payload
        checksum = 0
        for b in body:
            checksum ^= b

        frame = header + body + bytes([checksum])

        with self._lock:
            self._ser.write(frame)

    def _msp_read_frame(self, expected_cmd: Optional[int] = None, timeout: float = 0.2) -> Tuple[int, bytes]:
        """Lit un frame MSP v1 (depuis FC). Retourne (cmd_id, payload)."""
        if not self._ser:
            raise RuntimeError("Port série non ouvert")

        self._ser.timeout = timeout

        # Cherche header '$M<'
        start = b''
        while start != b'$M<':
            ch = self._ser.read(1)
            if not ch:
                raise TimeoutError("Timeout MSP en lisant header")
            start = (start + ch)[-3:]

        # longueur + cmd
        length_bytes = self._ser.read(1)
        cmd_bytes = self._ser.read(1)
        if len(length_bytes) < 1 or len(cmd_bytes) < 1:
            raise TimeoutError("Timeout MSP longueur/cmd")

        length = length_bytes[0]
        cmd = cmd_bytes[0]

        payload = self._ser.read(length)
        if len(payload) < length:
            raise TimeoutError("Timeout MSP payload")

        checksum_rx = self._ser.read(1)
        if len(checksum_rx) < 1:
            raise TimeoutError("Timeout MSP checksum")

        checksum_calc = 0
        for b in (length_bytes + cmd_bytes + payload):
            checksum_calc ^= b
        if checksum_calc != checksum_rx[0]:
            raise ValueError("Checksum MSP invalide")

        if expected_cmd is not None and cmd != expected_cmd:
            # On pourrait ignorer ou rebuffer ; ici on lève
            raise ValueError(f"MSP cmd inattendu: {cmd}, attendu {expected_cmd}")

        return cmd, payload

    def _msp_request(self, cmd: int, timeout: float = 0.2) -> bytes:
        """Envoie une requête MSP (payload vide) et lit la réponse."""
        self._msp_send(cmd, b'')
        _, payload = self._msp_read_frame(expected_cmd=cmd, timeout=timeout)
        return payload

    # ------------- Sécurité / arming -------------

    def is_ready_to_arm(self) -> bool:
        """Check simple, à adapter selon ton setup."""
        if self.battery.voltage < 10.0:
            return False
        # Si tu veux exiger GPS 3D:
        # if self.gps.fix_type < 3 or self.gps.sats < 6:
        #     return False
        return True

    def arm(self):
        """Arme le drone via canal ARM (AUX)."""
        # Suppose que CH5 (AUX1) est le switch ARM : 1000=OFF, 2000=ON
        self.set_rc_override({5: 2000})
        self.armed = True

    def disarm(self):
        self.set_rc_override({5: 1000})
        self.armed = False

    def emergency_stop(self):
        """Désarmement immédiat."""
        self.disarm()

    # ------------- Modes de vol via AUX -------------

    def set_mode(self, mode: str):
        """
        Change le mode via les canaux AUX.
        À adapter en fonction de ta config INAV (onglet Modes).
        Exemples ici :
          - CH6 : ANGLE / POSHOLD / NAV_WP selon la zone
          - CH7 : RTH
        """
        overrides = {}

        if mode == "ANGLE":
            overrides[6] = 1200  # zone ANGLE
        elif mode == "POSHOLD":
            overrides[6] = 1500  # zone POSHOLD
        elif mode == "NAV_WP":
            overrides[6] = 1800  # zone NAV_WP
        elif mode == "RTH":
            overrides[7] = 1800
        else:
            raise ValueError(f"Mode inconnu: {mode}")

        self.set_rc_override(overrides)
        self.nav.mode = mode

    # ------------- RC override -------------

    def enable_rc_override(self):
        """
        Active la transmission continue des canaux RC via MSP.
        REQUIS pour contrôler le drone via MSP (arming, modes, etc.).

        NOTE: Assurez-vous que iNav est configuré pour MSP RX ou MSP Override:
        - Configurator > Receiver: set serialrx_provider = MSP
        - OU: Configuration MSP Override dans les versions récentes d'iNav
        """
        self._rc_override_enabled = True
        print("[INavDrone] RC override activé (transmission continue à", 1.0/self.rc_update_interval, "Hz)")

    def disable_rc_override(self):
        """Désactive la transmission continue MSP RC."""
        self._rc_override_enabled = False
        print("[INavDrone] RC override désactivé")

    def set_rc_override(self, channels: Dict[int, int]):
        """
        Met à jour les valeurs des canaux RC : dict {num_channel: valeur 1000..2000}.

        Si RC override est activé, les nouvelles valeurs seront envoyées automatiquement
        par la boucle _rc_loop. Sinon, cette fonction envoie immédiatement les valeurs.

        Args:
            channels: Dictionnaire {canal: valeur}, ex: {1: 1500, 5: 2000}
        """
        # Mets à jour notre état local
        for ch, val in channels.items():
            self.rc_channels[ch] = val

        # Si le override n'est pas activé, envoyer immédiatement (mode legacy)
        if not self._rc_override_enabled:
            self._send_rc_channels()

    def _send_rc_channels(self):
        """
        Envoie les canaux RC actuels via MSP_SET_RAW_RC.
        Appelé automatiquement par _rc_loop si RC override est activé.
        """
        # MSP_SET_RAW_RC envoie 8 canaux (min) en uint16 LE
        max_ch = max(self.rc_channels.keys())
        n = max(8, max_ch)  # on envoie au moins 8
        values = [self.rc_channels.get(i, 1500) for i in range(1, n + 1)]
        payload = struct.pack('<' + 'H' * n, *values)
        self._msp_send(self.MSP_SET_RAW_RC, payload)

    # ------------- Navigation haut niveau -------------

    def go_to(self, lat_deg: float, lon_deg: float, alt_m: float, radius_m: float = 2.0, wp_no: int = 255):
        """
        Va vers un point GPS (lat/lon/alt) en utilisant MSP_SET_WP sur un waypoint spécial (par défaut 255).

        Format iNav MSP_SET_WP (21 octets):
          wp_no (uint8), action (uint8), lat (int32), lon (int32), alt (int32),
          p1 (int16), p2 (int16), p3 (int16), flag (uint8)

        Args:
            lat_deg: Latitude en degrés
            lon_deg: Longitude en degrés
            alt_m: Altitude en mètres (relative au home par défaut)
            radius_m: Rayon de waypoint (non utilisé directement dans MSP_SET_WP)
            wp_no: Numéro de waypoint (255 = position cible pour Follow-Me/GCS NAV)
        """
        # Conversion en unités MSP
        lat_i = int(lat_deg * 1e7)
        lon_i = int(lon_deg * 1e7)
        alt_i = int(alt_m * 100)  # cm

        # Action : 1 = WAYPOINT (simple point de navigation)
        action = 1

        # Paramètres (p1: speed cm/s, p2: unused, p3: altitude mode bits)
        p1 = 0      # vitesse par défaut (0 = utiliser config FC)
        p2 = 0      # non utilisé
        p3 = 0      # 0 = altitude relative au home

        # Flag : 0 = waypoint normal, 0xa5 = dernier waypoint
        flag = 0

        # Payload MSP_SET_WP format iNav complet (21 octets)
        payload = struct.pack(
            '<BBlllhhhB',
            wp_no,
            action,
            lat_i,
            lon_i,
            alt_i,
            p1,
            p2,
            p3,
            flag
        )
        self._msp_send(self.MSP_SET_WP, payload)

        # Met en mode NAV_WP pour que iNAV suive ce WP
        self.set_mode("NAV_WP")

    def follow_path(self, wps: List[Tuple[float, float, float]], radius_m: float = 2.0):
        """
        Suit une liste de waypoints [(lat, lon, alt), ...] en séquence.
        Version simple bloquante.
        """
        for (lat, lon, alt) in wps:
            print(f"[INavDrone] GoTo {lat:.7f}, {lon:.7f}, {alt:.1f} m")
            self.go_to(lat, lon, alt, radius_m)
            # Attente naïve : tu peux améliorer en utilisant la distance réelle
            time.sleep(2.0)

    def climb_to(self, target_alt_m: float, tol_m: float = 1.0, use_estimated_alt: bool = True):
        """
        Monte/descend jusqu'à target_alt_m en gardant la position lat/lon actuelle.
        Utilise go_to(...) avec même lat/lon et altitude différente.

        Args:
            target_alt_m: Altitude cible en mètres (relative au home)
            tol_m: Tolérance d'altitude en mètres
            use_estimated_alt: Utiliser l'altitude estimée du FC (recommandé) ou GPS
        """
        if self.gps.lat is None or self.gps.lon is None:
            raise RuntimeError("Pas de GPS pour climb_to")

        self.go_to(self.gps.lat, self.gps.lon, target_alt_m)

        # Boucle de convergence
        while self._running:
            current_alt = self.altitude.estimated_alt if use_estimated_alt else self.gps.alt
            if current_alt is not None and abs(current_alt - target_alt_m) <= tol_m:
                break
            time.sleep(0.2)

    def hold_here(self):
        """Maintient la position actuelle (GPS poshold) via le mode POSHOLD."""
        self.set_mode("POSHOLD")

    def return_to_home(self):
        """Active le mode RTH d'iNAV."""
        self.set_mode("RTH")

    # ------------- Helpers takeoff / land -------------

    def takeoff(self, target_alt: float = 5):
        """
        Décollage automatique : arme, passe en POSHOLD, et monte à l'altitude cible.

        Args:
            target_alt: Altitude cible en mètres (défaut: 5m)
        """
        self.arm()
        self.set_mode("POSHOLD")
        self.climb_to(target_alt)

    def land(self):
        """
        Atterrissage automatique : descente douce vers le sol puis désarmement.
        Descend à 0.5m avec une tolérance de 0.5m, puis désarme.
        """
        self.climb_to(0.5, tol_m=0.5)
        self.disarm()
