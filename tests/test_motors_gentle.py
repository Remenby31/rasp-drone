#!/usr/bin/env python3
"""
Test moteurs TRÈS DOUX - Montée progressive ultra-lente
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
print("🐌 TEST MOTEURS - MONTÉE ULTRA-DOUCE")
print("=" * 60)
print("\n⚠️  HÉLICES RETIRÉES ? Drone bien fixé ?")
print("\nDémarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/6] Connexion...")
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/6] Configuration canaux (throttle idle)...")
    rc = {1: 1500, 2: 1500, 3: 1000, 4: 1500, 5: 1000}
    for _ in range(40):
        send_rc_channels(ser, rc)
        time.sleep(0.05)
    print("✓ Canaux stabilisés")

    print("\n[3/6] Armement...")
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

    print("\n[4/6] 🚀 Montée TRÈS progressive du throttle...")
    print("   1000 → 1150µs sur 5 secondes (par pas de 10µs)")

    # Montée de 1000 à 1150 par pas de 10µs
    for throttle in range(1000, 1151, 10):
        rc[3] = throttle

        # Envoyer 5 fois (0.25s à chaque niveau)
        for _ in range(5):
            send_rc_channels(ser, rc)
            time.sleep(0.05)

        if throttle % 50 == 0:
            print(f"   Throttle: {throttle}µs")

    print("\n[5/6] Maintien 1150µs pendant 2 secondes...")
    rc[3] = 1150
    for _ in range(40):
        send_rc_channels(ser, rc)
        time.sleep(0.05)
    print("✓ Test terminé")

    print("\n[6/6] Descente et désarmement...")
    # Descente progressive
    for throttle in range(1150, 999, -50):
        rc[3] = throttle
        for _ in range(5):
            send_rc_channels(ser, rc)
            time.sleep(0.05)

    rc[3] = 1000
    for _ in range(10):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    # Désarmer
    rc[5] = 1000
    for _ in range(20):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    print("✓ Désarmé")

    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ")
    print("=" * 60)
    print("\n❓ Les moteurs ont-ils tourné ?")
    print("\nSi OUI:")
    print("  🎉 SUCCÈS TOTAL! Le contrôle MSP fonctionne parfaitement!")
    print("\nSi NON:")
    print("  → Vérifie que 'enable_pwm_output = ON' dans CLI")
    print("  → Teste manuellement dans Motors tab de Configurator")

    ser.close()

except KeyboardInterrupt:
    print("\n\n⚠️  ARRÊT D'URGENCE!")
    try:
        rc[3] = 1000
        rc[5] = 1000
        for _ in range(10):
            send_rc_channels(ser, rc)
            time.sleep(0.05)
        ser.close()
        print("✓ Arrêté proprement")
    except:
        pass
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
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
