#!/usr/bin/env python3
"""
Test moteurs avec vérification complète de l'état d'armement via MSP
⚠️ HÉLICES RETIRÉES OBLIGATOIRE ⚠️
"""

from inav_drone import INavDrone
import time
import sys
import struct

def read_msp_status(drone):
    """Lit MSP_STATUS pour vérifier l'état d'armement"""
    try:
        # MSP_STATUS = 101
        payload = drone._msp_request(101, timeout=0.5)
        if len(payload) >= 11:
            cycle_time, i2c_errors, sensors, flags, config_profile = struct.unpack('<HHHIB', payload[:11])
            armed = (flags & 0x01) != 0  # Bit 0 = armed
            print(f"   MSP_STATUS: flags=0x{flags:04x}, armed={armed}")
            return armed
        return False
    except Exception as e:
        print(f"   Erreur lecture MSP_STATUS: {e}")
        return False

def read_msp_motor(drone):
    """Lit MSP_MOTOR pour voir les valeurs des moteurs"""
    try:
        # MSP_MOTOR = 104
        payload = drone._msp_request(104, timeout=0.5)
        if len(payload) >= 8:
            # 4 moteurs minimum (uint16 chacun)
            num_motors = len(payload) // 2
            motors = struct.unpack('<' + 'H' * num_motors, payload)
            print(f"   MSP_MOTOR: {motors}")
            return motors
        return None
    except Exception as e:
        print(f"   Erreur lecture MSP_MOTOR: {e}")
        return None

print("=" * 60)
print("⚠️  TEST MOTEURS - Contrôle total via MSP")
print("=" * 60)

print("\nDémarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/8] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/8] Lecture état initial...")
    print(f"   Batterie: {drone.battery.voltage:.1f}V")
    armed_before = read_msp_status(drone)
    if armed_before:
        print("   ⚠️  Drone DÉJÀ armé!")
    else:
        print("   ✓ Drone désarmé")

    print("\n[3/8] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif (50Hz)")

    print("\n[4/8] Configuration canaux RC - Throttle IDLE...")
    drone.set_rc_override({
        1: 1500,  # Roll centre
        2: 1500,  # Pitch centre
        3: 1000,  # Throttle IDLE (IMPORTANT pour armer)
        4: 1500,  # Yaw centre
        5: 1000,  # ARM switch OFF
        6: 1000,  # Modes
        7: 1000,
        8: 1000
    })
    time.sleep(1.0)
    print("✓ Canaux configurés")

    print("\n[5/8] Armement via canal ARM (CH5=2000)...")
    drone.set_rc_override({5: 2000})

    # Attendre et vérifier plusieurs fois
    for i in range(5):
        time.sleep(0.5)
        armed = read_msp_status(drone)
        if armed:
            print(f"   ✓ Drone ARMÉ après {(i+1)*0.5:.1f}s!")
            break
        else:
            print(f"   Tentative {i+1}/5: Pas encore armé...")

    if not armed:
        print("\n❌ Le drone ne s'arme pas!")
        print("Raisons possibles:")
        print("  - Vérifiez dans iNAV Configurator > Setup les raisons du blocage")
        print("  - Calibration gyro nécessaire ?")
        print("  - Sécurité activée (angle trop important?) ")
        print("  - CH5 pas configuré comme ARM dans l'onglet Modes ?")
        drone.disconnect()
        sys.exit(1)

    print("\n[6/8] Lecture des valeurs moteurs avant throttle...")
    motors_before = read_msp_motor(drone)

    print("\n[7/8] ⚡ ACTIVATION MOTEURS - 1200µs pendant 1 seconde...")
    drone.set_rc_override({3: 1200})
    time.sleep(0.5)

    # Vérifier que les moteurs ont changé de valeur
    motors_during = read_msp_motor(drone)

    time.sleep(0.5)
    print("✓ Test terminé")

    # Retour idle
    drone.set_rc_override({3: 1000})
    time.sleep(0.5)

    print("\n[8/8] Désarmement...")
    drone.set_rc_override({5: 1000})
    time.sleep(1.0)

    armed_after = read_msp_status(drone)
    if not armed_after:
        print("✓ Désarmé")
    else:
        print("⚠️  Toujours armé! Désarmement forcé...")
        drone.emergency_stop()
        time.sleep(1.0)

    print("\n" + "=" * 60)
    print("📊 RÉSULTAT DU TEST")
    print("=" * 60)
    print(f"Moteurs avant throttle: {motors_before}")
    print(f"Moteurs avec throttle:  {motors_during}")

    if motors_before and motors_during:
        if motors_during != motors_before:
            print("\n✅ Les valeurs moteurs ont CHANGÉ!")
            print("   → Les moteurs devraient avoir bougé")
        else:
            print("\n⚠️  Les valeurs moteurs n'ont PAS changé")
            print("   → Problème: ESCs non alimentés? PWM désactivé?")

    print("\nMoteurs ont-ils tourné physiquement ?")

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
