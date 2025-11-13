#!/usr/bin/env python3
"""
Test armement SANS thread télémétrie qui interfère
Approche minimaliste : seulement RC override + vérification armement
"""

import serial
import struct
import time
import sys

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
        # Cherche header
        start = b''
        while start != b'$M>':
            ch = ser.read(1)
            if not ch:
                raise TimeoutError("Timeout header")
            start = (start + ch)[-3:]

        # Lit le reste
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

        # Vérifier checksum
        checksum_calc = 0
        for b in (length_bytes + cmd_bytes + payload):
            checksum_calc ^= b
        if checksum_calc != checksum_rx[0]:
            continue

        # Si c'est la bonne commande, retourner
        if expected_cmd is None or cmd == expected_cmd:
            return payload

    raise TimeoutError(f"Timeout waiting for cmd {expected_cmd}")

def send_rc_channels(ser, channels):
    """Envoie MSP_SET_RAW_RC (200)"""
    values = [channels.get(i, 1500) for i in range(1, 9)]
    payload = struct.pack('<HHHHHHHH', *values)
    msp_send(ser, 200, payload)

def check_armed(ser):
    """Vérifie si armé via MSP_STATUS (101)"""
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
print("🎯 TEST ARMEMENT CLEAN - Sans télémétrie")
print("=" * 60)
print("\nScript minimaliste sans threads qui interfèrent\n")

print("Démarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/6] Ouverture port série...")
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    time.sleep(1.0)
    print("✓ Port ouvert")

    print("\n[2/6] Vérification état initial...")
    armed, flags = check_armed(ser)
    print(f"   Armed: {armed}, Flags: 0x{flags:08x}")

    print("\n[3/6] Configuration canaux RC - Throttle IDLE...")
    rc = {
        1: 1500,  # Roll
        2: 1500,  # Pitch
        3: 1000,  # Throttle IDLE (CRITIQUE!)
        4: 1500,  # Yaw
        5: 1000,  # ARM OFF
        6: 1000,
        7: 1000,
        8: 1000
    }

    # Envoyer en continu pendant 2s pour que le FC voie le signal
    print("   Envoi continu pendant 2s...")
    for _ in range(40):  # 40 x 50ms = 2s
        send_rc_channels(ser, rc)
        time.sleep(0.05)
    print("✓ Canaux configurés et stabilisés")

    print("\n[4/6] 🔓 ARMEMENT - CH5 à 2000...")
    rc[5] = 2000  # ARM ON

    # Envoyer RC + vérifier armement en boucle
    armed = False
    for i in range(50):  # 50 x 100ms = 5s max
        send_rc_channels(ser, rc)

        # Vérifier armement toutes les 10 itérations (500ms)
        if i % 10 == 0:
            armed, flags = check_armed(ser)
            print(f"   [{i*0.1:.1f}s] Armed: {armed}, Flags: 0x{flags:08x}")

            if armed:
                print(f"\n   ✅ DRONE ARMÉ après {i*0.1:.1f}s!")
                break

        time.sleep(0.05)  # 50ms entre chaque envoi = 20Hz

    if armed:
        print("\n[5/6] ✓ Maintien armé pendant 2 secondes...")
        for _ in range(40):
            send_rc_channels(ser, rc)
            time.sleep(0.05)
    else:
        print("\n[5/6] ⚠️  Pas armé après 5 secondes")

    print("\n[6/6] 🔒 Désarmement...")
    rc[5] = 1000  # ARM OFF
    for _ in range(20):
        send_rc_channels(ser, rc)
        time.sleep(0.05)

    time.sleep(0.5)
    armed_final, flags_final = check_armed(ser)
    print(f"   Armed: {armed_final}, Flags: 0x{flags_final:08x}")

    print("\n" + "=" * 60)
    print("📊 RÉSULTAT")
    print("=" * 60)

    if armed:
        print("\n🎉 SUCCÈS! Le drone s'est armé via MSP!")
        print("   → La communication MSP fonctionne")
        print("   → Le contrôle RC via MSP fonctionne")
        print("   → L'armement via MSP fonctionne!")
    else:
        print("\n❌ ÉCHEC: Le drone ne s'arme toujours pas")
        print("\nRaisons possibles:")
        print("  1. Sécurité iNAV bloque (calibration, angle, etc.)")
        print("  2. Mode ARM mal configuré dans Modes")
        print("  3. PREARM requis mais non configuré")
        print("  4. receiver_type = MSP ne fonctionne pas comme prévu")
        print("\nSOLUTION ULTIME:")
        print("  → Connectez le FC au PC avec iNAV Configurator")
        print("  → Onglet Setup : regardez les icônes rouges")
        print("  → Elles indiquent EXACTEMENT pourquoi l'armement est bloqué")

    ser.close()

except KeyboardInterrupt:
    print("\n⚠️  INTERRUPTION!")
    try:
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
