# Utilisation du CLI iNAV depuis Python

Ce document explique comment utiliser le script `send_cli_command.py` pour envoyer des commandes CLI à iNAV directement depuis le Raspberry Pi.

---

## 🚀 Usage Rapide

```bash
# Commande simple
python3 send_cli_command.py "get receiver_type"

# Commande avec paramètre
python3 send_cli_command.py "set beeper_off_flags = DISARMING"

# Plusieurs commandes (ex: configuration + save)
python3 send_cli_command.py "set beeper_off_flags = DISARMING" "save"

# Voir l'état complet du FC
python3 send_cli_command.py "status"
```

---

## 📋 Exemples Pratiques

### Lire une configuration

```bash
# Lire le type de receiver
python3 send_cli_command.py "get receiver_type"

# Lire les flags beeper
python3 send_cli_command.py "get beeper_off_flags"

# Lire le protocole moteur
python3 send_cli_command.py "get motor_pwm_protocol"

# Lire l'état PWM outputs
python3 send_cli_command.py "get enable_pwm_output"
```

### Modifier une configuration

```bash
# Désactiver les bips au désarmement
python3 send_cli_command.py "set beeper_off_flags = DISARMING" "save"

# Changer le protocole moteur
python3 send_cli_command.py "set motor_pwm_protocol = ONESHOT125" "save"

# Activer/désactiver PWM outputs
python3 send_cli_command.py "set enable_pwm_output = ON" "save"
```

### Diagnostic

```bash
# État complet du FC
python3 send_cli_command.py "status"

# Voir toutes les features actives
python3 send_cli_command.py "feature"

# Voir la configuration des modes (AUX)
python3 send_cli_command.py "aux"

# Voir les ports série
python3 send_cli_command.py "serial"
```

### Désactiver les bips ESC (Exemples complets)

```bash
# Désactiver TOUS les bips
python3 send_cli_command.py "set beeper_off_flags = ALL" "save"

# Désactiver seulement le bip de désarmement
python3 send_cli_command.py "set beeper_off_flags = DISARMING" "save"

# Désactiver plusieurs bips spécifiques
python3 send_cli_command.py "set beeper_off_flags = ARMING,DISARMING,RX_LOST" "save"

# Réactiver tous les bips
python3 send_cli_command.py "set beeper_off_flags = " "save"
```

---

## 🐍 Utilisation dans du code Python

### Import et utilisation de base

```python
from send_cli_command import INavCLI

# Créer l'instance
cli = INavCLI(port='/dev/ttyACM0', baudrate=115200)

# Connexion
cli.connect()
cli.enter_cli()

# Envoyer une commande
response = cli.send_command("get receiver_type")
print(response)

# Modifier une configuration
cli.send_command("set beeper_off_flags = DISARMING")
cli.send_command("save")

# Quitter
cli.exit_cli()
cli.close()
```

### Exemple avec gestion d'erreurs

```python
from send_cli_command import INavCLI

cli = INavCLI()

try:
    cli.connect()
    cli.enter_cli()

    # Lire une valeur
    receiver_type = cli.send_command("get receiver_type")
    print(f"Receiver type: {receiver_type}")

    # Modifier et sauvegarder
    cli.send_command("set beeper_off_flags = DISARMING")
    cli.send_command("save")

    cli.exit_cli()

except Exception as e:
    print(f"Erreur: {e}")

finally:
    cli.close()
```

### Intégration avec INavDrone

```python
from inav_drone import INavDrone
from send_cli_command import INavCLI
import time

# Configuration via CLI avant de démarrer le drone
cli = INavCLI()
cli.connect()
cli.enter_cli()
cli.send_command("set beeper_off_flags = DISARMING")
cli.send_command("save")
cli.exit_cli()
cli.close()

# Attendre redémarrage
time.sleep(2.0)

# Maintenant utiliser INavDrone normalement
drone = INavDrone("/dev/ttyACM0", baudrate=115200)
drone.connect()
# ... vol autonome ...
drone.disconnect()
```

---

## ⚠️ Notes Importantes

### 1. Exclusivité du port série

**⚠️ Vous ne pouvez pas utiliser CLI et MSP en même temps !**

Quand vous entrez en mode CLI :
- Le FC quitte le mode MSP
- Les commandes MSP_SET_RAW_RC ne fonctionnent plus
- Le drone ne peut PAS être armé en mode CLI

**Workflow correct :**
```
1. Configurer via CLI (send_cli_command.py)
2. Quitter CLI (exit)
3. Attendre 1-2 secondes
4. Utiliser MSP (INavDrone)
```

### 2. Commande 'save' obligatoire

Les modifications ne sont PAS persistantes sans `save` :

```bash
# ❌ MAUVAIS - Sera perdu au redémarrage
python3 send_cli_command.py "set beeper_off_flags = DISARMING"

# ✅ BON - Sauvegardé dans EEPROM
python3 send_cli_command.py "set beeper_off_flags = DISARMING" "save"
```

### 3. Redémarrage après 'save'

La commande `save` redémarre automatiquement le FC :
- Attendre 2-3 secondes après `save` avant de se reconnecter
- Les connexions MSP actives seront fermées

### 4. Mode CLI bloque l'armement

**ARMING_DISABLED_CLI** sera actif tant que vous êtes en CLI :
- Toujours quitter avec `exit`
- Vérifier avec `status` que CLI n'est plus actif

---

## 🔍 Commandes CLI Utiles

### Lecture d'informations

| Commande | Description |
|----------|-------------|
| `status` | État complet du FC (armement, flags, etc.) |
| `version` | Version firmware iNAV |
| `diff` | Voir toutes les modifications par rapport aux defaults |
| `feature` | Lister les features actives |
| `aux` | Configuration des modes (ARM, ANGLE, etc.) |
| `serial` | Configuration des ports série |
| `get <param>` | Lire un paramètre spécifique |

### Configuration

| Commande | Description |
|----------|-------------|
| `set <param> = <value>` | Modifier un paramètre |
| `save` | Sauvegarder dans EEPROM et redémarrer |
| `defaults` | Réinitialiser aux valeurs par défaut (⚠️ DANGER) |

### Diagnostic

| Commande | Description |
|----------|-------------|
| `tasks` | Voir les tâches en cours et leur temps |
| `rxfail` | Configuration failsafe |
| `resource` | Mapping des pins hardware |

---

## 📚 Exemples de Configuration Complète

### Configuration initiale pour MSP

```bash
python3 send_cli_command.py \
  "set receiver_type = MSP" \
  "set nav_extra_arming_safety = ALLOW_BYPASS" \
  "feature VCP" \
  "set enable_pwm_output = ON" \
  "save"
```

### Configurer ARM et PREARM

```bash
python3 send_cli_command.py \
  "aux 1 0 0 1700 2100" \
  "aux 1 51 0 1700 2100" \
  "save"
```

### Désactiver les bips et optimiser pour autonome

```bash
python3 send_cli_command.py \
  "set beeper_off_flags = DISARMING,RX_LOST,RX_SET" \
  "set nav_extra_arming_safety = ALLOW_BYPASS" \
  "save"
```

---

## 🛠️ Dépannage

### Le script ne se connecte pas

```bash
# Vérifier que le port existe
ls -l /dev/ttyACM0

# Vérifier les permissions
sudo chmod 666 /dev/ttyACM0

# Ou ajouter l'utilisateur au groupe dialout (permanent)
sudo usermod -a -G dialout $USER
# Puis se reconnecter
```

### Pas de réponse aux commandes

- Le FC est peut-être déjà en mode CLI (envoi de '#' échoue)
- Essayez de fermer iNAV Configurator si ouvert
- Débranchez/rebranchez le FC

### Commande 'save' ne fonctionne pas

- Assurez-vous que le paramètre existe : `get <param>` avant `set`
- Vérifiez qu'il n'y a pas d'erreur de syntaxe
- Certains paramètres nécessitent des valeurs spécifiques

### "ARMING_DISABLED_CLI" après utilisation

- Vous n'avez pas quitté le CLI avec `exit`
- Le script devrait appeler `cli.exit_cli()` automatiquement
- Déconnectez/reconnectez le FC pour forcer la sortie

---

## 🎯 Workflow Recommandé

### Pour tests/développement

```python
# 1. Configuration initiale (une fois)
cli = INavCLI()
cli.connect()
cli.enter_cli()
cli.send_command("set receiver_type = MSP")
cli.send_command("set enable_pwm_output = ON")
cli.send_command("save")
cli.close()

time.sleep(2)

# 2. Vol autonome
drone = INavDrone("/dev/ttyACM0")
drone.connect()
drone.enable_rc_override()
# ... contrôle drone ...
drone.disconnect()
```

### Pour production/vol autonome

```python
# Séparer configuration (au démarrage) et vol

# script_config.py
from send_cli_command import INavCLI

def configure_fc():
    cli = INavCLI()
    cli.connect()
    cli.enter_cli()
    cli.send_command("set beeper_off_flags = DISARMING")
    cli.send_command("save")
    cli.close()

# script_flight.py
from inav_drone import INavDrone

def autonomous_flight():
    drone = INavDrone("/dev/ttyACM0")
    drone.connect()
    # ... mission autonome ...
    drone.disconnect()
```

---

**Date de création** : 2025-11-13
**Testé avec** : iNAV 8.0.1, OMNIBUS F4 V3
**Statut** : ✅ Fonctionnel
