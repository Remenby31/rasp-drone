#!/usr/bin/env python3
"""
Lit les arming flags détaillés via MSP pour savoir EXACTEMENT
pourquoi le drone ne s'arme pas
"""

import serial
import struct
import time

def msp_send(ser, cmd, payload=b''):
    """Envoie une commande MSP"""
    length = len(payload)
    header = b'$M<'
    body = bytes([length, cmd]) + payload
    checksum = 0
    for b in body:
        checksum ^= b
    frame = header + body + bytes([checksum])
    ser.write(frame)

def msp_read(ser, expected_cmd, timeout=0.5):
    """Lit une réponse MSP"""
    ser.timeout = timeout
    start_time = time.time()

    while time.time() - start_time < timeout:
        start = b''
        while start != b'$M>':
            ch = ser.read(1)
            if not ch:
                raise TimeoutError("Timeout header")
            start = (start + ch)[-3:]

        length_bytes = ser.read(1)
        cmd_bytes = ser.read(1)
        if len(length_bytes) < 1 or len(cmd_bytes) < 1:
            continue

        length = length_bytes[0]
        cmd = cmd_bytes[0]
        payload = ser.read(length)
        checksum_rx = ser.read(1)

        if len(payload) < length or len(checksum_rx) < 1:
            continue

        checksum_calc = 0
        for b in (length_bytes + cmd_bytes + payload):
            checksum_calc ^= b
        if checksum_calc != checksum_rx[0]:
            continue

        if expected_cmd is None or cmd == expected_cmd:
            return payload

    raise TimeoutError(f"Timeout waiting for cmd {expected_cmd}")

def decode_arming_flags(flags):
    """Décode les flags d'armement"""
    flag_names = {
        0x00000001: "ARMED",
        0x00000002: "WAS_EVER_ARMED",
        0x00000100: "ARMING_DISABLED_RC_NOT_LEVEL",
        0x00000200: "ARMING_DISABLED_SENSORS_CALIBRATING",
        0x00000400: "ARMING_DISABLED_SYSTEM_OVERLOADED",
        0x00000800: "ARMING_DISABLED_NAVIGATION_UNSAFE",
        0x00001000: "ARMING_DISABLED_COMPASS_NOT_CALIBRATED",
        0x00002000: "ARMING_DISABLED_ACCELEROMETER_NOT_CALIBRATED",
        0x00004000: "ARMING_DISABLED_ARM_SWITCH",
        0x00008000: "ARMING_DISABLED_HARDWARE_FAILURE",
        0x00010000: "ARMING_DISABLED_BOXFAILSAFE",
        0x00020000: "ARMING_DISABLED_BOXKILLSWITCH",
        0x00040000: "ARMING_DISABLED_RC_LINK",
        0x00080000: "ARMING_DISABLED_THROTTLE",
        0x00100000: "ARMING_DISABLED_CLI",
        0x00200000: "ARMING_DISABLED_CMS_MENU",
        0x00400000: "ARMING_DISABLED_OSD_MENU",
        0x00800000: "ARMING_DISABLED_ROLLPITCH_NOT_CENTERED",
        0x01000000: "ARMING_DISABLED_SERVO_AUTOTRIM",
        0x02000000: "ARMING_DISABLED_OOM",
        0x04000000: "ARMING_DISABLED_INVALID_SETTING",
        0x08000000: "ARMING_DISABLED_PWM_OUTPUT_ERROR",
        0x10000000: "ARMING_DISABLED_NO_PREARM",
        0x20000000: "ARMING_DISABLED_DSHOTBEEPER",
        0x40000000: "ARMING_DISABLED_LANDING_DETECTED",
        0x80000000: "ARMING_DISABLED_OTHER",
    }

    active_flags = []
    for bit, name in flag_names.items():
        if flags & bit:
            active_flags.append((bit, name))

    return active_flags

print("=" * 60)
print("🔍 DIAGNOSTIC ARMING - Lecture flags détaillés")
print("=" * 60)

try:
    print("\n[1/3] Connexion...")
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/3] Lecture MSP_STATUS...")
    msp_send(ser, 101)  # MSP_STATUS
    payload = msp_read(ser, 101, timeout=1.0)

    if len(payload) >= 11:
        cycle_time, i2c_errors, sensors, flags, config_profile = struct.unpack('<HHHIB', payload[:11])

        print(f"\n📊 ÉTAT DU FC:")
        print(f"   Cycle Time: {cycle_time} µs")
        print(f"   I2C Errors: {i2c_errors}")
        print(f"   Sensors: 0x{sensors:04x}")
        print(f"   Flags: 0x{flags:08x}")
        print(f"   Profile: {config_profile}")

        # Décoder les sensors
        print(f"\n🔧 CAPTEURS ACTIFS:")
        if sensors & 0x01: print("   ✓ ACC (Accelerometer)")
        if sensors & 0x02: print("   ✓ BARO (Barometer)")
        if sensors & 0x04: print("   ✓ MAG (Magnetometer)")
        if sensors & 0x08: print("   ✓ GPS")
        if sensors & 0x10: print("   ✓ RANGEFINDER")
        if sensors & 0x20: print("   ✓ GYRO")

        # Décoder les flags d'armement
        print(f"\n🚨 ARMING FLAGS:")
        active_flags = decode_arming_flags(flags)

        if not active_flags:
            print("   ✓ Aucun flag actif (devrait pouvoir s'armer!)")
        else:
            for bit, name in active_flags:
                if "ARMED" in name and not "DISABLED" in name:
                    print(f"   ✅ 0x{bit:08x}: {name}")
                else:
                    print(f"   ❌ 0x{bit:08x}: {name}")

    print("\n[3/3] Interprétation...")

    # Flags les plus courants
    if flags & 0x00040000:
        print("\n❌ ARMING_DISABLED_RC_LINK")
        print("   → Le FC ne détecte pas de lien RC valide")
        print("   → receiver_type = MSP configuré ?")
        print("   → Les canaux RC sont-ils reçus en continu ?")

    if flags & 0x00000200:
        print("\n❌ ARMING_DISABLED_SENSORS_CALIBRATING")
        print("   → Les capteurs (gyro/acc) sont en cours de calibration")
        print("   → Attendez quelques secondes")

    if flags & 0x00000800:
        print("\n❌ ARMING_DISABLED_NAVIGATION_UNSAFE")
        print("   → Navigation considérée comme non sûre")
        print("   → GPS fix insuffisant ?")
        print("   → nav_extra_arming_safety = ALLOW_BYPASS ?")

    if flags & 0x00080000:
        print("\n❌ ARMING_DISABLED_THROTTLE")
        print("   → Le throttle n'est pas à idle (1000µs)")
        print("   → Assurez-vous que CH3 = 1000")

    if flags & 0x00004000:
        print("\n❌ ARMING_DISABLED_ARM_SWITCH")
        print("   → Le switch ARM n'est pas dans la bonne position")
        print("   → CH5 doit être > 1700 pour armer")

    if flags & 0x10000000:
        print("\n❌ ARMING_DISABLED_NO_PREARM")
        print("   → PREARM requis mais pas activé")
        print("   → Configurez PREARM dans l'onglet Modes")

    if flags & 0x04000000:
        print("\n❌ ARMING_DISABLED_INVALID_SETTING")
        print("   → Configuration invalide détectée par iNAV")
        print("   → Vérifiez la configuration dans Configurator")

    if flags == 0x00000000:
        print("\n✅ AUCUN FLAG DE BLOCAGE!")
        print("   → Le FC devrait pouvoir s'armer")
        print("   → Mais s'il ne s'arme pas, c'est un bug ou un blocage caché")

    print("\n" + "=" * 60)
    print("💡 SOLUTION")
    print("=" * 60)
    print("\nSi les flags ne montrent rien :")
    print("  1. Ouvrez iNAV Configurator")
    print("  2. Onglet Setup > Regardez les icônes en haut")
    print("  3. Elles montrent visuellement ce qui bloque")
    print("  4. Faites une capture d'écran et envoyez-la moi")

    ser.close()

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
