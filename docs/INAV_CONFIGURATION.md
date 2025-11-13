# Configuration iNAV pour contrôle MSP

Ce document liste toutes les configurations nécessaires dans iNAV 8.0.1 pour permettre le contrôle du drone via MSP (Raspberry Pi).

## Matériel testé
- **Flight Controller** : OMNIBUS F4 V3
- **Firmware** : iNAV 8.0.1
- **Raspberry Pi** : Connexion USB
- **Port détecté** : `/dev/ttyACM0`

---

## 1. Configuration CLI iNAV

### Activer MSP comme source RC

```bash
set receiver_type = MSP
```

**Explication** : Configure iNAV pour accepter les commandes RC via MSP au lieu d'un récepteur radio physique.

**Valeurs possibles** : `NONE`, `SERIAL`, `MSP`, `SIM`

---

### Désactiver les sécurités de navigation

```bash
set nav_extra_arming_safety = ALLOW_BYPASS
```

**Explication** : Permet d'armer le drone sans fix GPS, utile pour les tests en intérieur.

**Valeurs possibles** : `ON`, `ALLOW_BYPASS`

---

### Activer la feature VCP (Virtual COM Port)

Dans l'onglet **Configuration** de iNAV Configurator :
- Cochez la case **"VCP"** dans la section "Other Features"
- Ou via CLI :

```bash
feature VCP
```

**Explication** : Active la communication série USB pour MSP.

---

### Sauvegarder et redémarrer

```bash
save
```

Le FC va automatiquement redémarrer avec les nouvelles configurations.

---

## 2. Configuration des Ports (iNAV Configurator)

### Onglet "Ports"

Vérifiez que **MSP** est activé sur les ports suivants :
- **USB-VCP** : MSP activé (automatique avec `feature VCP`)
- **UART6** : MSP à 115200 bauds (si vous utilisez connexion série GPIO)

---

## 3. Configuration des Modes (iNAV Configurator)

### Onglet "Modes"

**Mode ARM :**
- Canal : **AUX 1** (CH5)
- Range : **1300 - 2100**

**Configuration :**
1. Cliquez sur **"Add Range"** pour le mode **ARM**
2. Sélectionnez **AUX 1**
3. Réglez le range de 1300 à 2100
4. Cliquez **"Save"**

---

## 4. Configuration des Outputs (Optionnel)

### Onglet "Outputs"

**Important** : Pour les tests moteurs, les sorties PWM doivent être activées.

Dans l'onglet Outputs :
- Activez **"Enable motor and servo output"** (bouton en haut)
- ⚠️ **Ceci est temporaire** et se désactive à chaque déconnexion (sécurité)

---

## 5. Résumé des commandes CLI

Voici toutes les commandes à exécuter dans la CLI iNAV :

```bash
# Configurer MSP comme source RC
set receiver_type = MSP

# Permettre armement sans GPS
set nav_extra_arming_safety = ALLOW_BYPASS

# Activer VCP pour USB
feature VCP

# Sauvegarder et redémarrer
save
```

---

## 6. Vérification de la configuration

### Vérifier receiver_type
```bash
get receiver_type
```
Devrait afficher : `receiver_type = MSP`

### Vérifier nav_extra_arming_safety
```bash
get nav_extra_arming_safety
```
Devrait afficher : `nav_extra_arming_safety = ALLOW_BYPASS`

### Vérifier que VCP est activé
```bash
feature
```
Devrait lister **VCP** dans les features actives.

---

## 7. Protocole MSP utilisé

### Headers MSP v1
- **Requête** (Raspberry Pi → FC) : `$M<`
- **Réponse** (FC → Raspberry Pi) : `$M>`

### Commandes MSP utilisées dans le code

| Commande | ID | Description |
|----------|-----|-------------|
| MSP_RC | 105 | Lecture canaux RC |
| MSP_RAW_GPS | 106 | Lecture GPS |
| MSP_ATTITUDE | 108 | Lecture attitude (roll/pitch/yaw) |
| MSP_ALTITUDE | 109 | Lecture altitude |
| MSP_ANALOG | 110 | Lecture batterie |
| MSP_STATUS | 101 | État du FC (armé/désarmé) |
| MSP_MOTOR | 104 | Valeurs moteurs |
| MSP_SET_RAW_RC | 200 | Envoi canaux RC |

### Fréquence d'envoi MSP_SET_RAW_RC
- **Minimum requis** : 5 Hz (200ms)
- **Utilisé dans le code** : 50 Hz (20ms)
- **Important** : En dessous de 5Hz, le FC passe en failsafe RC

---

## 8. Canaux RC via MSP

### Valeurs PWM
- **Minimum** : 1000 µs
- **Centre** : 1500 µs
- **Maximum** : 2000 µs

### Mapping des canaux

| Canal | Fonction | Idle | Actif |
|-------|----------|------|-------|
| CH1 | Roll | 1500 | 1000-2000 |
| CH2 | Pitch | 1500 | 1000-2000 |
| CH3 | Throttle | 1000 | 1000-2000 |
| CH4 | Yaw | 1500 | 1000-2000 |
| CH5 | ARM | 1000 (OFF) | 2000 (ON) |
| CH6 | Mode switch | 1000-2000 | Variable |
| CH7 | RTH | 1000 (OFF) | 2000 (ON) |
| CH8 | Libre | 1500 | Variable |

---

## 9. Séquence d'armement via MSP

1. **Activer RC override** : `drone.enable_rc_override()`
2. **Configurer tous les canaux** :
   - CH1-4 : Centre (1500)
   - CH3 : Throttle à idle (1000) **OBLIGATOIRE pour armer**
   - CH5 : Désarmé (1000)
3. **Armer** : CH5 = 2000
4. **Attendre 2-3 secondes** que l'armement soit effectif
5. **Envoyer throttle** : CH3 = 1100-1200 (très faible)
6. **Désarmer** : CH3 = 1000, puis CH5 = 1000

---

## 10. Dépannage

### Le drone ne s'arme pas

**Vérifications :**
1. `receiver_type` est bien à `MSP` ?
2. Mode ARM configuré sur CH5 dans l'onglet Modes ?
3. Throttle à 1000 (idle) avant d'armer ?
4. Dans l'onglet Setup, quelles icônes sont rouges/barrées ?

**Commandes de diagnostic :**
```bash
# Voir l'état du receiver
get receiver_type

# Voir les paramètres d'armement
get nav_extra_arming_safety

# Voir toutes les features actives
feature
```

### Les moteurs ne tournent pas

**Causes possibles :**
1. ⚠️ **Sorties PWM désactivées** (onglet Outputs)
2. ESCs non alimentés ou non connectés
3. Drone pas réellement armé (vérifier MSP_STATUS)
4. Throttle trop faible (< 1100µs)

### Timeout MSP

**Solutions :**
1. Vérifier que le câble USB est bien branché
2. Vérifier que VCP est activé (`feature VCP`)
3. Essayer de débrancher/rebrancher le FC
4. Vérifier qu'iNAV Configurator n'est pas connecté en même temps

---

## 11. Tests de sécurité

### ⚠️ AVANT TOUT TEST MOTEUR

- ✅ **Hélices RETIRÉES**
- ✅ Drone sur surface stable
- ✅ Personne à proximité
- ✅ Prêt à débrancher la batterie

### Tests progressifs recommandés

1. **Test connexion** : `test_connection_usb.py` (lecture seule)
2. **Test armement** : `test_motors_msp_full.py` (vérifie l'armement)
3. **Test moteurs faible** : `test_motors_quick.py` (1200µs, 1s)
4. **Test moteurs progressif** : `test_motors_v2.py` (1050→1150µs)

---

## 12. Références

- [iNAV Wiki - Remote Management](https://github.com/iNavFlight/inav/wiki/INAV-Remote-Management,-Control-and-Telemetry)
- [iNAV 8.0 Release Notes](https://github.com/iNavFlight/inav/wiki/8.0.0-Release-Notes)
- [MSP Protocol Documentation](https://github.com/iNavFlight/inav/blob/master/docs/MSP_V2.md)
- [Example MSP_SET_RAW_RC](https://github.com/stronnag/msp_set_rx)

---

**Date de création** : 2025-11-13
**Version iNAV testée** : 8.0.1
**Statut** : Configuration validée, communication MSP opérationnelle ✅
