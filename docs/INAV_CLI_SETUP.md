# Configuration iNAV CLI - Guide Complet

Ce document contient toutes les commandes CLI iNAV nécessaires pour configurer le contrôle MSP depuis un Raspberry Pi.

---

## 🚀 Configuration Minimale Requise

Ouvrez iNAV Configurator, allez dans l'onglet **CLI**, et tapez ces commandes :

```bash
# 1. Configurer le receiver en mode MSP
set receiver_type = MSP

# 2. Bypass les sécurités de navigation (optionnel mais recommandé pour tests)
set nav_extra_arming_safety = ALLOW_BYPASS

# 3. Activer la communication USB (VCP = Virtual COM Port)
feature VCP

# 4. CRITIQUE: Activer les sorties PWM/DSHOT
set enable_pwm_output = ON

# 5. Sauvegarder et redémarrer
save
```

**⚠️ La commande `set enable_pwm_output = ON` est CRITIQUE !**
Sans elle, les moteurs ne tourneront jamais même si tout le reste fonctionne.

---

## 🎮 Configuration des Modes (AUX)

Les modes ARM et PREARM doivent être configurés sur le même canal (CH5 / AUX1) avec le même range :

```bash
# ARM sur CH5 (AUX1), activé entre 1700-2100µs
aux 1 0 0 1700 2100

# PREARM sur CH5 (AUX1), activé entre 1700-2100µs
aux 1 51 0 1700 2100

# Sauvegarder
save
```

**Explication des paramètres :**
- `aux 1` = Mixer profile 1
- `0` = Mode ARM (ID 0)
- `51` = Mode PREARM (ID 51)
- `0` = Canal AUX 1 (= CH5)
- `1700 2100` = Range d'activation

**⚠️ IMPORTANT :**
Si PREARM a un range trop large (ex: 900-2100), il sera toujours actif et **bloquera l'armement** !

---

## 🔧 Configuration Moteurs (Optionnel)

Si vous voulez ajuster les paramètres moteurs :

```bash
# Protocole moteur (DSHOT300 par défaut)
get motor_pwm_protocol
# Options: STANDARD, ONESHOT125, MULTISHOT, DSHOT150, DSHOT300, DSHOT600

# Si problèmes avec DSHOT, passer en ONESHOT125
set motor_pwm_protocol = ONESHOT125

# Fréquence PWM
get motor_pwm_rate
# Devrait être 16000 pour DSHOT300

# Throttle minimum (idle)
get min_command
# Devrait être 1000

# Vérifier que les outputs sont activés
get enable_pwm_output
# DOIT être ON
```

---

## 📊 Vérification de la Configuration

### Vérifier receiver_type

```bash
get receiver_type
# Doit retourner: receiver_type = MSP
```

### Vérifier les features actives

```bash
feature
# Doit contenir: VCP
```

### Vérifier les modes configurés

```bash
aux
# Devrait montrer:
# aux 1 0 0 1700 2100    (ARM)
# aux 1 51 0 1700 2100   (PREARM)
```

### Vérifier les sorties PWM

```bash
get enable_pwm_output
# DOIT retourner: enable_pwm_output = ON
```

### Vérifier l'état d'armement

```bash
status
# Regardez la ligne "Arming disabled flags:"
# Devrait être vide ou ne contenir que des flags temporaires
```

---

## 🛠️ Dépannage

### Le drone refuse de s'armer

1. **Vérifier les flags d'armement :**
   ```bash
   status
   ```
   Regardez la ligne `Arming disabled flags:`. Les blocages courants :
   - `RX` : Pas de lien RC (normal au démarrage avant MSP)
   - `CLI` : Sortez du CLI avec `exit`
   - `NOPREARM` : PREARM mal configuré (range trop large)
   - `THROTTLE` : Throttle pas à idle (1000µs)

2. **Corriger PREARM si nécessaire :**
   ```bash
   aux 1 51 0 1700 2100
   save
   ```

3. **Sortir du CLI :**
   ```bash
   exit
   ```

### Les moteurs ne tournent pas

1. **Vérifier les outputs PWM (cause la plus fréquente) :**
   ```bash
   get enable_pwm_output
   ```
   Si `OFF`, activez-le :
   ```bash
   set enable_pwm_output = ON
   save
   ```

2. **Tester manuellement dans Configurator :**
   - Onglet "Motors"
   - Activer "Motor test mode"
   - Bouger les sliders
   - Si ça marche → Problème de throttle minimum MSP
   - Si ça ne marche pas → Problème ESC/câblage

3. **Essayer un autre protocole :**
   ```bash
   set motor_pwm_protocol = ONESHOT125
   save
   ```

### MSP ne se connecte pas

1. **Vérifier VCP :**
   ```bash
   feature
   ```
   Si VCP absent :
   ```bash
   feature VCP
   save
   ```

2. **Vérifier les ports série :**
   ```bash
   serial
   ```
   USB-VCP devrait avoir MSP activé.

---

## 📝 Configuration Complète (Copy-Paste)

Voici la configuration complète à copier-coller dans le CLI :

```bash
# Receiver MSP
set receiver_type = MSP
set nav_extra_arming_safety = ALLOW_BYPASS

# Features
feature VCP

# Outputs (CRITIQUE!)
set enable_pwm_output = ON

# Modes ARM et PREARM
aux 1 0 0 1700 2100    # ARM sur CH5
aux 1 51 0 1700 2100   # PREARM sur CH5

# Sauvegarder et redémarrer
save
```

Après le redémarrage, vérifiez avec :

```bash
# Vérifier receiver
get receiver_type

# Vérifier features
feature

# Vérifier outputs (IMPORTANT!)
get enable_pwm_output

# Vérifier modes
aux

# Vérifier armement
status
```

---

## ✅ Checklist de Configuration

Avant de tester le contrôle MSP, vérifiez :

- [ ] `receiver_type = MSP`
- [ ] `feature VCP` activé
- [ ] **`enable_pwm_output = ON`** (CRITIQUE!)
- [ ] Mode ARM configuré : `aux 1 0 0 1700 2100`
- [ ] Mode PREARM configuré : `aux 1 51 0 1700 2100`
- [ ] CLI fermé (tapez `exit` avant de tester)
- [ ] Batterie connectée (15V+)
- [ ] Hélices retirées pour tests moteurs

---

## 🎯 Commandes de Diagnostic

### Lire toutes les configurations importantes

```bash
# Receiver
get receiver_type
get nav_extra_arming_safety

# Features
feature

# Moteurs
get motor_pwm_protocol
get motor_pwm_rate
get min_command
get enable_pwm_output

# Modes
aux

# État système
status
```

### Réinitialiser la configuration (⚠️ DANGER)

```bash
# Réinitialiser AUX DEFAULTS (efface tous les réglages!)
defaults nosave

# Ne faites ceci QUE si vous voulez tout recommencer!
```

---

## 📚 Références

- **iNAV Wiki MSP** : https://github.com/iNavFlight/inav/wiki/INAV-Remote-Management,-Control-and-Telemetry
- **iNAV CLI Commands** : https://github.com/iNavFlight/inav/blob/master/docs/Cli.md
- **MSP Protocol** : https://github.com/iNavFlight/inav/wiki/MSP-V2

---

**Date de création** : 2025-11-13
**Firmware testé** : iNAV 8.0.1
**Flight Controller** : OMNIBUS F4 V3
**Statut** : ✅ Configuration validée et fonctionnelle
