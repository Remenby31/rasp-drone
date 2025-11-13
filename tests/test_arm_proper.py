#!/usr/bin/env python3
"""
Test armement CORRECT selon documentation iNAV
1. Interroge les box IDs (modes)
2. Lit MSP_BOXNAMES pour identifier ARM
3. Configure correctement les switches
4. Tente l'armement
"""

from inav_drone import INavDrone
import time
import sys
import struct

def read_msp_boxnames(drone):
    """Lit MSP_BOXNAMES (116) pour avoir les noms des modes"""
    try:
        payload = drone._msp_request(116, timeout=1.0)
        if len(payload) > 0:
            # Les noms sont séparés par des ';'
            names = payload.decode('ascii').rstrip(';').split(';')
            print(f"\n   📦 {len(names)} Box modes trouvés:")
            for i, name in enumerate(names):
                print(f"      Box {i}: {name}")
            return names
        return []
    except Exception as e:
        print(f"   ❌ Erreur MSP_BOXNAMES: {e}")
        return []

def read_msp_activeboxes(drone):
    """Lit MSP_ACTIVEBOXES (113) pour voir quels modes sont actifs"""
    try:
        payload = drone._msp_request(113, timeout=0.5)
        active = []
        for i in range(len(payload) * 8):
            byte_idx = i // 8
            bit_idx = i % 8
            if byte_idx < len(payload):
                if payload[byte_idx] & (1 << bit_idx):
                    active.append(i)
        return active
    except Exception as e:
        print(f"   ❌ Erreur MSP_ACTIVEBOXES: {e}")
        return []

def read_msp_status(drone):
    """Lit MSP_STATUS"""
    try:
        payload = drone._msp_request(101, timeout=0.5)
        if len(payload) >= 11:
            cycle_time, i2c_errors, sensors, flags, config_profile = struct.unpack('<HHHIB', payload[:11])
            armed = (flags & 0x01) != 0
            return armed, flags
        return False, 0
    except Exception as e:
        print(f"   ❌ Erreur MSP_STATUS: {e}")
        return False, 0

print("=" * 60)
print("🎯 TEST ARMEMENT PROPER - Avec interrogation FC")
print("=" * 60)

print("\nDémarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/8] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    time.sleep(1.5)
    print("✓ Connecté")

    print("\n[2/8] Interrogation FC - Lecture box names...")
    box_names = read_msp_boxnames(drone)

    # Trouver l'index du mode ARM
    arm_box_id = -1
    if "ARM" in box_names:
        arm_box_id = box_names.index("ARM")
        print(f"\n   ✅ Mode ARM trouvé à l'index {arm_box_id}")
    else:
        print("\n   ❌ Mode ARM non trouvé dans les box names!")

    print("\n[3/8] État initial...")
    print(f"   Batterie: {drone.battery.voltage:.1f}V")
    armed, flags = read_msp_status(drone)
    print(f"   Armed: {armed}, Flags: 0x{flags:08x}")

    active_before = read_msp_activeboxes(drone)
    print(f"   Boxes actifs: {active_before}")

    print("\n[4/8] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif (50Hz)")

    print("\n[5/8] Configuration canaux RC - Throttle IDLE...")
    drone.set_rc_override({
        1: 1500,  # Roll
        2: 1500,  # Pitch
        3: 1000,  # Throttle IDLE (CRITIQUE)
        4: 1500,  # Yaw
        5: 1000,  # ARM OFF
        6: 1000,
        7: 1000,
        8: 1000
    })
    time.sleep(1.0)
    print("✓ Canaux configurés")

    # Vérifier que le FC les reçoit
    print(f"\n   Vérification réception:")
    print(f"   CH3 (Throttle): {drone.rc_channels.get(3, 0)} µs (doit être ~1000)")
    print(f"   CH5 (ARM): {drone.rc_channels.get(5, 0)} µs (doit être ~1000)")

    print("\n[6/8] 🔓 Armement - CH5 à 2000...")
    drone.set_rc_override({5: 2000})
    time.sleep(0.5)

    # Vérifier que CH5 change
    ch5_val = drone.rc_channels.get(5, 0)
    print(f"   CH5 reçu par FC: {ch5_val} µs")

    if ch5_val < 1900:
        print(f"   ⚠️  CH5 pas à 2000! Problème d'envoi MSP")

    # Vérifier les boxes actifs
    time.sleep(0.5)
    active_after = read_msp_activeboxes(drone)
    print(f"   Boxes actifs après CH5=2000: {active_after}")

    if arm_box_id >= 0:
        if arm_box_id in active_after:
            print(f"   ✅ Box ARM (#{arm_box_id}) est ACTIF!")
        else:
            print(f"   ❌ Box ARM (#{arm_box_id}) PAS actif malgré CH5=2000")
            print(f"      → Le mode ARM ne se déclenche pas avec CH5")

    print("\n[7/8] Vérification armement...")
    armed = False
    for i in range(5):
        time.sleep(0.5)
        armed, flags = read_msp_status(drone)

        if armed:
            print(f"\n   ✅ DRONE ARMÉ après {(i+1)*0.5:.1f}s!")
            break
        else:
            print(f"   Tentative {i+1}/5: pas armé (flags=0x{flags:08x})")

    if armed:
        print("\n   Attente 1 seconde armé...")
        time.sleep(1.0)

    print("\n[8/8] 🔒 Désarmement...")
    drone.set_rc_override({5: 1000})
    time.sleep(0.5)

    armed_after, flags_after = read_msp_status(drone)
    print(f"   Armed: {armed_after}, Flags: 0x{flags_after:08x}")

    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC FINAL")
    print("=" * 60)

    if armed:
        print("\n🎉 SUCCÈS! Le drone s'est armé!")
    else:
        print("\n❌ ÉCHEC: Le drone ne s'arme pas")
        print("\nDIAGNOSTIC:")

        if ch5_val >= 1900:
            print("  ✅ CH5 arrive bien à 2000 au FC")
        else:
            print(f"  ❌ CH5 ne change pas (reçu: {ch5_val})")

        if arm_box_id >= 0:
            if arm_box_id in active_after:
                print(f"  ✅ Box ARM (#{arm_box_id}) s'active avec CH5=2000")
                print("     → Le switch fonctionne MAIS le drone ne s'arme pas")
                print("     → Cause: Sécurité iNAV bloque l'armement")
                print("     → Solution: Vérifiez Setup > Arming dans Configurator")
            else:
                print(f"  ❌ Box ARM (#{arm_box_id}) ne s'active PAS")
                print("     → Le range dans l'onglet Modes est incorrect")
                print("     → Recréez le mode ARM avec range 1800-2100")
        else:
            print("  ❌ Mode ARM introuvable dans les box names")

    drone.disconnect()

except KeyboardInterrupt:
    print("\n⚠️  INTERRUPTION!")
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    sys.exit(1)
