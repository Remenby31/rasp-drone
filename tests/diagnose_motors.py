#!/usr/bin/env python3
"""
Diagnostic complet pour comprendre pourquoi les moteurs ne tournent pas
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

def read_motor_values(ser):
    """Lit MSP_MOTOR (104) pour voir les valeurs envoyées aux moteurs"""
    try:
        msp_send(ser, 104)
        payload = msp_read(ser, 104, timeout=0.5)

        # Chaque moteur = 2 bytes (uint16)
        num_motors = len(payload) // 2
        motors = []
        for i in range(num_motors):
            motor_val = struct.unpack('<H', payload[i*2:(i+1)*2])[0]
            motors.append(motor_val)
        return motors
    except Exception as e:
        print(f"   Erreur lecture MSP_MOTOR: {e}")
        return []

def read_servo_values(ser):
    """Lit MSP_SERVO (103) pour debug"""
    try:
        msp_send(ser, 103)
        payload = msp_read(ser, 103, timeout=0.5)
        num_servos = len(payload) // 2
        servos = []
        for i in range(num_servos):
            servo_val = struct.unpack('<H', payload[i*2:(i+1)*2])[0]
            servos.append(servo_val)
        return servos
    except Exception as e:
        return []

def send_rc_channels(ser, channels):
    """Envoie MSP_SET_RAW_RC (200)"""
    values = [channels.get(i, 1500) for i in range(1, 9)]
    payload = struct.pack('<HHHHHHHH', *values)
    msp_send(ser, 200, payload)

def check_armed(ser):
    """Vérifie si armé"""
    msp_send(ser, 101)
    try:
        payload = msp_read(ser, 101, timeout=0.3)
        if len(payload) >= 11:
            _, _, _, flags, _ = struct.unpack('<HHHIB', payload[:11])
            armed = (flags & 0x01) != 0
            return armed, flags
    except:
        pass
    return False, 0

print("=" * 60)
print("🔍 DIAGNOSTIC MOTEURS")
print("=" * 60)

try:
    print("\n[1/6] Connexion...")
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/6] Lecture valeurs moteurs AVANT armement...")
    motors_before = read_motor_values(ser)
    print(f"   Moteurs: {motors_before}")

    print("\n[3/6] Configuration et armement...")
    rc = {
        1: 1500,
        2: 1500,
        3: 1000,  # Throttle idle
        4: 1500,
        5: 1000,  # ARM OFF
    }

    # Envoi RC pendant 2s
    for _ in range(40):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    # Armer
    rc[5] = 2000
    armed = False
    for i in range(50):
        send_rc_channels(ser, rc)
        if i % 10 == 0:
            armed, flags = check_armed(ser)
            if armed:
                print(f"   ✅ ARMÉ!")
                break
        time.sleep(0.05)

    if not armed:
        print("   ❌ Échec armement")
        ser.close()
        exit(1)

    print("\n[4/6] Lecture valeurs moteurs APRÈS armement (throttle idle)...")
    time.sleep(0.2)
    motors_armed_idle = read_motor_values(ser)
    print(f"   Moteurs: {motors_armed_idle}")

    print("\n[5/6] Throttle à 1200 - Lecture valeurs moteurs...")
    rc[3] = 1200

    # Envoyer pendant 1 seconde
    for i in range(20):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    time.sleep(0.2)
    motors_throttle = read_motor_values(ser)
    print(f"   Moteurs: {motors_throttle}")

    # Retour idle
    rc[3] = 1000
    for _ in range(10):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    print("\n[6/6] Désarmement...")
    rc[5] = 1000
    for _ in range(20):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    print("\n" + "=" * 60)
    print("📊 ANALYSE")
    print("=" * 60)

    print(f"\n1. Moteurs AVANT armement: {motors_before}")
    print(f"   → Devrait être [1000, 1000, 1000, 1000] ou proche")

    print(f"\n2. Moteurs APRÈS armement (idle): {motors_armed_idle}")
    print(f"   → Devrait rester à ~1000 (min_command)")

    print(f"\n3. Moteurs avec throttle 1200: {motors_throttle}")
    print(f"   → Devrait augmenter à ~1200 ou plus")

    if motors_throttle == motors_armed_idle:
        print("\n❌ PROBLÈME: Les valeurs moteurs ne changent PAS!")
        print("\nCauses possibles:")
        print("  1. Throttle minimum (min_throttle) trop élevé dans iNAV")
        print("  2. Mixer désactivé ou mal configuré")
        print("  3. Mode PASSTHROUGH actif qui bloque les moteurs")
        print("  4. Configuration moteurs dans Outputs mal faite")
        print("\nSOLUTION:")
        print("  → Ouvre iNAV Configurator")
        print("  → Onglet Motors : essaye de bouger les sliders")
        print("  → Si ça marche là, c'est un problème de throttle mapping")
    elif all(m > 1000 for m in motors_throttle):
        print("\n✅ Les valeurs moteurs CHANGENT correctement!")
        print("\nSi les moteurs physiques ne tournent pas:")
        print("  1. ESCs pas alimentés (BEC 5V uniquement ne suffit pas)")
        print("  2. ESCs pas calibrés pour iNAV")
        print("  3. Câblage moteurs/ESCs incorrect")
        print("  4. PWM protocole incompatible (essayez ONESHOT125)")

    ser.close()

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    try:
        ser.close()
    except:
        pass
