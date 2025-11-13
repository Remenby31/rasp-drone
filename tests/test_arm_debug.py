#!/usr/bin/env python3
"""
Test armement avec debug complet via MSP
"""

from inav_drone import INavDrone
import time
import sys
import struct

def read_msp_status(drone):
    """Lit MSP_STATUS pour vérifier l'état et les flags"""
    try:
        payload = drone._msp_request(101, timeout=0.5)
        if len(payload) >= 11:
            cycle_time, i2c_errors, sensors, flags, config_profile = struct.unpack('<HHHIB', payload[:11])
            armed = (flags & 0x01) != 0

            print(f"   MSP_STATUS:")
            print(f"     Flags: 0x{flags:08x}")
            print(f"     Armed: {armed}")
            print(f"     Sensors: 0x{sensors:04x}")

            # Décoder les sensors actifs
            sensor_names = []
            if sensors & 0x01: sensor_names.append("ACC")
            if sensors & 0x02: sensor_names.append("BARO")
            if sensors & 0x04: sensor_names.append("MAG")
            if sensors & 0x08: sensor_names.append("GPS")
            if sensors & 0x10: sensor_names.append("RANGEFINDER")
            if sensors & 0x20: sensor_names.append("GYRO")
            print(f"     Sensors actifs: {', '.join(sensor_names) if sensor_names else 'Aucun'}")

            return armed, flags
        return False, 0
    except Exception as e:
        print(f"   ❌ Erreur lecture MSP_STATUS: {e}")
        return False, 0

def read_msp_boxids(drone):
    """Lit MSP_BOXIDS pour voir les modes disponibles"""
    try:
        payload = drone._msp_request(119, timeout=0.5)  # MSP_BOXIDS
        if len(payload) > 0:
            num_boxes = len(payload)
            print(f"   MSP_BOXIDS: {num_boxes} modes configurés")
            return True
        return False
    except Exception as e:
        print(f"   ❌ Erreur lecture MSP_BOXIDS: {e}")
        return False

print("=" * 60)
print("🔍 TEST ARMEMENT AVEC DEBUG MSP")
print("=" * 60)

print("\nDémarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/7] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    time.sleep(1.5)
    print("✓ Connecté")

    print("\n[2/7] Lecture état initial...")
    print(f"   Batterie: {drone.battery.voltage:.1f}V")
    armed_before, flags_before = read_msp_status(drone)

    print("\n[3/7] Vérification modes disponibles...")
    read_msp_boxids(drone)

    print("\n[4/7] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif")

    print("\n[5/7] Configuration canaux RC...")
    drone.set_rc_override({
        1: 1500,  # Roll
        2: 1500,  # Pitch
        3: 1000,  # Throttle IDLE
        4: 1500,  # Yaw
        5: 1000,  # ARM OFF
        6: 1000,
        7: 1000,
        8: 1000
    })
    time.sleep(1.0)
    print("✓ Canaux configurés")

    # Vérifier que le FC reçoit les canaux
    print("\n   Lecture des canaux RC reçus par le FC...")
    time.sleep(0.5)
    print(f"   CH1: {drone.rc_channels.get(1, 0)} µs")
    print(f"   CH2: {drone.rc_channels.get(2, 0)} µs")
    print(f"   CH3: {drone.rc_channels.get(3, 0)} µs")
    print(f"   CH4: {drone.rc_channels.get(4, 0)} µs")
    print(f"   CH5: {drone.rc_channels.get(5, 0)} µs")

    print("\n[6/7] 🔓 Tentative d'ARMEMENT...")
    drone.set_rc_override({5: 2000})

    # Vérifier plusieurs fois
    armed = False
    for i in range(6):
        time.sleep(0.5)
        armed, flags = read_msp_status(drone)

        if armed:
            print(f"\n   ✅ ARMÉ après {(i+1)*0.5:.1f}s!")
            break
        else:
            print(f"\n   Tentative {i+1}/6: Pas armé (flags=0x{flags:08x})")

            # Analyser les flags pour comprendre pourquoi
            if flags & 0x00000100:
                print("      → ARMING DISABLED: RC not configured")
            if flags & 0x00000200:
                print("      → ARMING DISABLED: Invalid hardware config")
            if flags & 0x00000400:
                print("      → ARMING DISABLED: Navigation unsafe")
            if flags & 0x00000800:
                print("      → ARMING DISABLED: Calibrating")
            if flags & 0x00001000:
                print("      → ARMING DISABLED: System overload")
            if flags & 0x04000000:
                print("      → ARMING DISABLED: Other (voir iNAV Configurator)")

    print("\n[7/7] 🔒 Désarmement...")
    drone.set_rc_override({5: 1000})
    time.sleep(0.5)

    armed_after, _ = read_msp_status(drone)
    if not armed_after:
        print("   ✅ Désarmé")
    else:
        print("   ⚠️  Forçage désarmement...")
        drone.emergency_stop()

    print("\n" + "=" * 60)
    print("📊 RÉSULTAT")
    print("=" * 60)

    if armed:
        print("\n🎉 SUCCÈS! Le drone s'est armé via MSP!")
    else:
        print("\n❌ ÉCHEC: Le drone ne s'arme pas")
        print("\nDIAGNOSTIC:")
        print("  1. Vérifiez dans iNAV Configurator > Setup les icônes rouges")
        print("  2. Vérifiez dans iNAV Configurator > Receiver si les barres bougent")
        print("  3. Vérifiez que receiver_type = MSP dans la CLI")
        print("  4. Essayez de calibrer le gyro (onglet Setup)")

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
