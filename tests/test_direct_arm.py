#!/usr/bin/env python3
"""
Test armement DIRECT via MSP_SET_MODE
Au lieu de simuler un switch RC, on envoie directement la commande ARM
"""

from inav_drone import INavDrone
import time
import sys
import struct

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
        print(f"   Erreur MSP_STATUS: {e}")
        return False, 0

def send_msp_arm_command(drone, arm: bool):
    """
    Envoie MSP_ARM/MSP_DISARM
    MSP_ARM = 151
    MSP_DISARM = 152
    """
    try:
        cmd = 151 if arm else 152
        drone._msp_send(cmd, b'')
        print(f"   Envoyé MSP_{'ARM' if arm else 'DISARM'}")
        time.sleep(0.1)
        return True
    except Exception as e:
        print(f"   Erreur: {e}")
        return False

print("=" * 60)
print("🔓 TEST ARMEMENT DIRECT via MSP")
print("=" * 60)
print("\nUtilise MSP_ARM au lieu de simuler un switch RC\n")

print("Démarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/6] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/6] État initial...")
    armed, flags = read_msp_status(drone)
    print(f"   Armed: {armed}, Flags: 0x{flags:08x}")

    print("\n[3/6] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif")

    print("\n[4/6] Configuration canaux (throttle idle)...")
    drone.set_rc_override({
        1: 1500,
        2: 1500,
        3: 1000,  # THROTTLE IDLE
        4: 1500,
        5: 1000,
    })
    time.sleep(1.0)
    print("✓ Canaux configurés")

    print("\n[5/6] 🔓 Envoi commande MSP_ARM directe...")
    send_msp_arm_command(drone, arm=True)

    # Vérifier plusieurs fois
    armed = False
    for i in range(5):
        time.sleep(0.5)
        armed, flags = read_msp_status(drone)

        if armed:
            print(f"\n   ✅ ARMÉ après {(i+1)*0.5:.1f}s!")
            break
        else:
            print(f"   Tentative {i+1}/5: pas armé (flags=0x{flags:08x})")

    if armed:
        print("\n   Attente 1 seconde armé...")
        time.sleep(1.0)

    print("\n[6/6] 🔒 Désarmement...")
    send_msp_arm_command(drone, arm=False)
    time.sleep(0.5)

    armed, flags = read_msp_status(drone)
    print(f"   Armed: {armed}, Flags: 0x{flags:08x}")

    print("\n" + "=" * 60)
    print("📊 RÉSULTAT")
    print("=" * 60)

    if armed:
        print("\n🎉 Le drone s'est armé via MSP_ARM !")
    else:
        print("\n❌ Échec avec MSP_ARM")
        print("\nLe drone ne peut probablement pas s'armer car:")
        print("  - Sécurité iNAV active (angle, calibration, etc.)")
        print("  - Utilisez une vraie radiocommande pour tester")

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
