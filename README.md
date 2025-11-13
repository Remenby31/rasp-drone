# INAV Drone Controller

Serveur Python pour Raspberry Pi permettant le contrôle autonome de drones INAV via le protocole MSP (MultiWii Serial Protocol).

## Description

Ce projet permet de contrôler un drone équipé du firmware INAV depuis un Raspberry Pi embarqué. Il communique avec le contrôleur de vol via le protocole MSP v1 et permet d'exécuter des missions de navigation GPS automatisées.

### Fonctionnalités

- **Télémétrie en temps réel**
  - Attitude (roll, pitch, yaw)
  - Position GPS (latitude, longitude, altitude, HDOP, ground course)
  - Altitude estimée du FC avec variomètre
  - État de la batterie (voltage, mAh consommés)
  - Canaux RC

- **Contrôle de vol**
  - Armement/désarmement du drone
  - Changement de modes de vol (ANGLE, POSHOLD, NAV_WP, RTH)
  - Override des canaux RC via MSP avec transmission continue (≥5Hz requis par iNav)

- **Navigation autonome**
  - `go_to()` : Navigation vers un point GPS spécifique
  - `follow_path()` : Suivi d'une série de waypoints
  - `climb_to()` : Montée/descente à une altitude cible
  - `hold_here()` : Maintien de position (GPS hold)
  - `return_to_home()` : Retour au point de départ
  - `takeoff()` / `land()` : Décollage et atterrissage automatiques

- **Sécurité**
  - Vérifications pré-armement
  - Arrêt d'urgence
  - Thread dédié pour la télémétrie

## Prérequis

### Matériel

- Raspberry Pi (3/4/5 ou Zero W)
- Drone équipé d'un contrôleur de vol avec firmware INAV
- Connexion série entre le Raspberry Pi et le FC (Flight Controller)
  - GPIO UART (pins TX/RX) ou
  - Adaptateur USB-TTL

### Logiciel

- Python 3.7+
- Bibliothèques Python :
  - `pyserial`

## Installation

1. Clonez le dépôt sur votre Raspberry Pi :

```bash
git clone <votre-repo>
cd rasp-drone
```

2. Installez les dépendances :

```bash
pip3 install pyserial
```

3. Activez l'UART sur le Raspberry Pi (si vous utilisez GPIO) :

```bash
sudo raspi-config
# Interface Options > Serial Port
# "Would you like a login shell..." > No
# "Would you like the serial port hardware..." > Yes
```

Redémarrez le Raspberry Pi après cette configuration.

## Configuration

### Configuration INAV - MSP RX (CRITIQUE)

**⚠️ Configuration obligatoire pour le contrôle MSP :**

Dans iNAV Configurator CLI, tapez :
```bash
set receiver_type = MSP
set nav_extra_arming_safety = ALLOW_BYPASS
feature VCP
set enable_pwm_output = ON
aux 1 0 0 1700 2100    # ARM sur CH5
aux 1 51 0 1700 2100   # PREARM sur CH5
save
```

**Pour plus de détails, consultez `docs/INAV_CLI_SETUP.md`**

**IMPORTANT** :
- iNav requiert que `MSP_SET_RAW_RC` soit envoyé **en continu à ≥5Hz**
- Ce code le fait automatiquement via `enable_rc_override()`
- `enable_pwm_output = ON` est CRITIQUE pour faire tourner les moteurs

### Configuration des modes de vol

Dans l'onglet **Modes** de l'interface INAV Configurator, configurez vos canaux AUX :

- **CH5 (AUX1)** : ARM (1000=Désarmé, 2000=Armé)
- **CH6 (AUX2)** : Modes de vol
  - 1000-1400 : ANGLE
  - 1400-1600 : POSHOLD
  - 1600-2000 : NAV WP
- **CH7 (AUX3)** : RTH (Return To Home)

Ajustez les valeurs dans `set_mode()` selon votre configuration.

### Port série

Le port série par défaut est `/dev/ttyAMA0` (UART GPIO sur Raspberry Pi).

Si vous utilisez un adaptateur USB, identifiez le port avec :

```bash
ls /dev/tty*
```

Les ports USB apparaissent généralement comme `/dev/ttyUSB0` ou `/dev/ttyACM0`.

## Utilisation

### Exemple de base

```python
from inav_drone import INavDrone
import time

# Connexion au drone
drone = INavDrone("/dev/ttyAMA0", baudrate=115200)
drone.connect()

# IMPORTANT: Activer le RC override pour contrôler via MSP
drone.enable_rc_override()

# Attendre que la télémétrie arrive
time.sleep(1.0)

# Afficher les métriques
print(f"Batterie : {drone.battery.voltage}V")
print(f"GPS : {drone.gps.lat}, {drone.gps.lon}")
print(f"Satellites : {drone.gps.sats}, Fix : {drone.gps.fix_type}")
print(f"Altitude estimée : {drone.altitude.estimated_alt}m")

# Vérifications de sécurité
if drone.is_ready_to_arm():
    # Décollage
    drone.arm()
    drone.set_mode("POSHOLD")
    drone.climb_to(10)  # Monte à 10m

    # Navigation vers un point GPS
    drone.go_to(48.858844, 2.294351, 15)  # Tour Eiffel, 15m d'altitude

    # Retour au point de départ
    drone.return_to_home()

    # Atterrissage
    drone.disarm()

# Déconnexion propre
drone.disconnect()
```

### Mission avec waypoints

```python
from inav_drone import INavDrone

drone = INavDrone("/dev/ttyAMA0")
drone.connect()
drone.enable_rc_override()  # IMPORTANT: Activer RC override

# Définir une mission avec plusieurs points
waypoints = [
    (48.8584, 2.2945, 10),  # Point 1
    (48.8590, 2.2950, 15),  # Point 2
    (48.8595, 2.2940, 10),  # Point 3
]

if drone.is_ready_to_arm():
    drone.takeoff(target_alt=10)
    drone.follow_path(waypoints, radius_m=2.0)
    drone.land()

drone.disconnect()
```

## Structure du projet

```
rasp-drone/
├── inav_drone.py           # Classe principale INavDrone
├── send_cli_command.py     # Script pour envoyer des commandes CLI
├── docs/                   # Documentation
│   ├── CLAUDE.md          # Journal de développement et découvertes
│   ├── CLI_USAGE.md       # Guide d'utilisation du CLI
│   ├── INAV_CLI_SETUP.md  # Configuration CLI complète
│   └── INAV_CONFIGURATION.md  # Configuration iNAV
├── examples/               # Scripts d'exemple
│   ├── main_basic.py      # Exemple basique
│   └── ...
├── tests/                  # Scripts de test
│   ├── test_arm_clean.py  # Test d'armement
│   ├── test_motors_gentle.py  # Test moteurs
│   ├── test_connection.py # Test connexion
│   └── ...
└── README.md              # Ce fichier
```

## Architecture

### Classe `INavDrone`

La classe principale offre une abstraction haut niveau pour le contrôle du drone :

**Connexion & Télémétrie**
- Thread dédié pour la mise à jour continue des métriques
- Polling automatique des données MSP (attitude, GPS, batterie, RC)
- Accès thread-safe au port série

**API de contrôle**
- Méthodes de navigation GPS haut niveau
- Gestion des modes de vol INAV
- Override des canaux RC

### Protocole MSP

Le projet utilise MSP v1 pour communiquer avec INAV :

| Commande MSP | ID  | Description |
|--------------|-----|-------------|
| MSP_RC       | 105 | Lecture des canaux RC |
| MSP_RAW_GPS  | 106 | Lecture GPS brut |
| MSP_ATTITUDE | 108 | Lecture attitude (angles) |
| MSP_ALTITUDE | 109 | Lecture altitude |
| MSP_ANALOG   | 110 | Lecture batterie |
| MSP_SET_RAW_RC | 200 | Override canaux RC |
| MSP_SET_WP   | 209 | Définir un waypoint |

## Sécurité

### Avant de voler

- Testez toujours en mode ANGLE avec le contrôleur manuel à portée
- Vérifiez que le GPS a un bon fix (8+ satellites)
- Vérifiez le niveau de batterie
- Testez l'arrêt d'urgence (`emergency_stop()`)
- Définissez correctement votre position HOME dans INAV

### Limites connues

- Le système n'intègre pas de détection d'obstacles
- La convergence vers les waypoints est approximative (basée sur des délais fixes)
- Pas de gestion de failsafe sophistiquée (utilisez les failsafes INAV)

## Personnalisation

### Modifier les modes de vol

Éditez la méthode `set_mode()` dans [inav_drone .py:252-274](inav_drone .py#L252-L274) pour correspondre à votre configuration INAV.

### Ajouter de nouvelles commandes MSP

Ajoutez l'ID de la commande MSP comme constante de classe, puis créez une méthode utilisant `_msp_request()` ou `_msp_send()`.

### Ajuster le polling

Modifiez `poll_interval` lors de l'initialisation :

```python
drone = INavDrone("/dev/ttyAMA0", poll_interval=0.05)  # 20 Hz
```

## Dépannage

### Le drone ne se connecte pas

- Vérifiez le câblage (TX -> RX, RX -> TX, GND commun)
- Vérifiez le port série : `ls -l /dev/ttyAMA0`
- Vérifiez le baudrate MSP dans INAV Configurator (généralement 115200)
- Testez avec `minicom` ou `screen` : `screen /dev/ttyAMA0 115200`

### Le GPS ne fonctionne pas

- Vérifiez la configuration GPS dans INAV (ports, protocole)
- Attendez le fix GPS (peut prendre plusieurs minutes à l'extérieur)
- Vérifiez `drone.gps.fix_type` et `drone.gps.sats`

### Le drone ne s'arme pas

- Vérifiez les raisons dans INAV Configurator (onglet Setup, icônes d'état)
- Vérifiez le niveau de batterie
- Vérifiez la calibration des capteurs
- Vérifiez que le mode ARM est bien configuré sur CH5

### Timeout MSP

- Réduisez `poll_interval` si le bus série est surchargé
- Vérifiez qu'aucun autre programme n'utilise le port série
- Augmentez le timeout dans `_msp_request()`

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

- Signaler des bugs
- Proposer de nouvelles fonctionnalités
- Améliorer la documentation
- Partager vos missions et cas d'usage

## Avertissement

Ce logiciel est fourni à des fins éducatives et expérimentales.

**L'utilisateur est seul responsable de l'utilisation de ce code et doit :**
- Respecter les réglementations aériennes locales
- Ne jamais voler au-dessus de personnes ou de zones interdites
- Toujours garder le contrôle visuel du drone
- Avoir un pilote de sécurité prêt à reprendre le contrôle manuel

**Utilisez ce code à vos propres risques.**

## Licence

[Ajoutez votre licence ici - MIT, GPL, Apache, etc.]

## Ressources

- [Documentation INAV](https://github.com/iNavFlight/inav/wiki)
- [Spécification MSP](https://github.com/iNavFlight/inav/wiki/MSP-V2)
- [Raspberry Pi GPIO](https://pinout.xyz/)
- [PySerial Documentation](https://pyserial.readthedocs.io/)

## Auteur

[Votre nom]

## Support

Pour toute question ou assistance, ouvrez une issue sur GitHub.
