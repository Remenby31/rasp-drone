#!/usr/bin/env python3
"""
Test moteurs avec throttle ÉLEVÉ (1600µs) + diagnostic MSP_MOTOR
⚠️ HÉLICES RETIRÉES OBLIGATOIRE ⚠️
"""

import serial
import struct
import time
import sys

def msp_send(ser, cmd, payload=b''):
    length = len(payload)
    header = b'$M<'
    body = bytes([length, cmd]) + payload
    checksum = 0
    for b in body:
        checksum ^= b
    frame = header + body + bytes([checksum])
    ser.write(frame)

def msp_read(ser, expected_cmd, timeout=0.5):
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

def send_rc_channels(ser, channels):
    values = [channels.get(i, 1500) for i in range(1, 9)]
    payload = struct.pack('<HHHHHHHH', *values)
    msp_send(ser, 200, payload)

def read_motor_values(ser):
    try:
        msp_send(ser, 104)
        payload = msp_read(ser, 104, timeout=0.5)
        num_motors = len(payload) // 2
        motors = []
        for i in range(num_motors):
            motor_val = struct.unpack('<H', payload[i*2:(i+1)*2])[0]
            motors.append(motor_val)
        return motors
    except:
        return []

def check_armed(ser):
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
print("🚀 TEST MOTEURS - THROTTLE ÉLEVÉ (1600µs)")
print("=" * 60)
print("\n⚠️  HÉLICES RETIRÉES ? Drone bien fixé ?")
print("\nDémarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/7] Connexion...")
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/7] Configuration canaux (throttle idle)...")
    rc = {1: 1500, 2: 1500, 3: 1000, 4: 1500, 5: 1000}
    for _ in range(40):
        send_rc_channels(ser, rc)
        time.sleep(0.05)
    print("✓ Canaux stabilisés")

    print("\n[3/7] Lecture MSP_MOTOR avant armement...")
    motors_before = read_motor_values(ser)
    print(f"   Moteurs: {motors_before}")

    print("\n[4/7] Armement...")
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
        sys.exit(1)

    print("\n[5/7] Test progressif du throttle...")

    throttle_levels = [1200, 1400, 1600]

    for throttle in throttle_levels:
        print(f"\n   🔹 Throttle: {throttle}µs")
        rc[3] = throttle

        # Envoyer pendant 2 secondes
        for _ in range(40):
            send_rc_channels(ser, rc)
            time.sleep(0.05)

        # Lire MSP_MOTOR
        time.sleep(0.1)
        motors = read_motor_values(ser)
        print(f"      MSP_MOTOR: {motors}")

        if throttle == 1600:
            print(f"\n   ⏱️  Maintien 1600µs pendant 3 secondes...")
            for _ in range(60):
                send_rc_channels(ser, rc)
                time.sleep(0.05)

    print("\n[6/7] Retour idle...")
    rc[3] = 1000
    for _ in range(20):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    print("\n[7/7] Désarmement...")
    rc[5] = 1000
    for _ in range(20):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    print("\n" + "=" * 60)
    print("📊 ANALYSE")
    print("=" * 60)

    print("\nLes moteurs ont-ils tourné ?")
    print("\nSi NON malgré MSP_MOTOR > 1500:")
    print("  1. Problème ESCs : pas de signal DSHOT ou mal calibrés")
    print("  2. Câblage signal moteurs incorrect")
    print("  3. ESCs ne supportent pas DSHOT300")
    print("\nSOLUTION:")
    print("  → Teste dans iNAV Configurator > Motors tab")
    print("  → Si ça ne marche pas là non plus:")
    print("     set motor_pwm_protocol = ONESHOT125")
    print("     save")

    ser.close()

except KeyboardInterrupt:
    print("\n⚠️  ARRÊT!")
    try:
        rc[3] = 1000
        rc[5] = 1000
        for _ in range(10):
            send_rc_channels(ser, rc)
            time.sleep(0.05)
        ser.close()
    except:
        pass
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    try:
        ser.close()
    except:
        pass
    sys.exit(1)
