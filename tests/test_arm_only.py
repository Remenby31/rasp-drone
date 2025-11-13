#!/usr/bin/env python3
"""
Test simple : Armer pendant 1 seconde puis désarmer
SANS activer les moteurs (throttle reste à idle)
"""

from inav_drone import INavDrone
import time
import sys
import struct

def read_msp_status(drone):
    """Lit MSP_STATUS pour vérifier l'état d'armement"""
    try:
        payload = drone._msp_request(101, timeout=0.5)
        if len(payload) >= 11:
            cycle_time, i2c_errors, sensors, flags, config_profile = struct.unpack('<HHHIB', payload[:11])
            armed = (flags & 0x01) != 0  # Bit 0 = armed
            return armed
        return False
    except Exception as e:
        print(f"   Erreur lecture MSP_STATUS: {e}")
        return False

print("=" * 60)
print("⚠️  TEST ARMEMENT SIMPLE - 1 seconde")
print("=" * 60)
print("\nThrottle restera à IDLE (1000µs)")
print("Les moteurs ne tourneront PAS\n")

print("Démarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/5] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/5] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif (50Hz)")

    print("\n[3/5] Configuration canaux - Throttle IDLE...")
    drone.set_rc_override({
        1: 1500,  # Roll
        2: 1500,  # Pitch
        3: 1000,  # Throttle IDLE (les moteurs ne tourneront pas)
        4: 1500,  # Yaw
        5: 1000,  # ARM OFF
    })
    time.sleep(0.5)
    print("✓ Canaux configurés")

    print("\n[4/5] 🔓 ARMEMENT pendant 1 seconde...")
    drone.set_rc_override({5: 2000})

    # Vérifier l'armement
    time.sleep(0.3)
    armed = read_msp_status(drone)

    if armed:
        print("   ✅ Drone ARMÉ!")
        print("   Throttle = 1000µs (idle, moteurs ne tournent pas)")
    else:
        print("   ⚠️  Pas armé...")

    # Rester armé 1 seconde
    time.sleep(0.7)

    print("\n[5/5] 🔒 Désarmement...")
    drone.set_rc_override({5: 1000})
    time.sleep(0.5)

    armed_after = read_msp_status(drone)
    if not armed_after:
        print("   ✅ Drone DÉSARMÉ")
    else:
        print("   ⚠️  Toujours armé! Désarmement forcé...")
        drone.emergency_stop()

    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ")
    print("=" * 60)

    if armed:
        print("\n🎉 Succès! Le drone s'est armé via MSP!")
        print("   → La configuration iNAV est correcte")
        print("   → Le contrôle RC via MSP fonctionne")
    else:
        print("\n❌ Le drone ne s'est pas armé")
        print("   → Vérifiez la configuration dans iNAV Configurator")

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
