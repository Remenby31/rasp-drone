#!/usr/bin/env python3
"""
Écoute passive du port série - capture toutes les données envoyées par le FC
"""

import serial
import time

print("=" * 60)
print("ÉCOUTE PASSIVE DU FC")
print("=" * 60)
print("\nÉcoute pendant 15 secondes...")
print("(Le FC peut envoyer des données MSP de manière automatique)\n")

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    start = time.time()
    total_bytes = 0

    while (time.time() - start) < 15:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            total_bytes += len(data)
            hex_str = ' '.join(f'{b:02x}' for b in data[:50])  # Premiers 50 bytes
            print(f"[+{time.time()-start:.1f}s] {len(data)} bytes: {hex_str}")

            if b'$M<' in data or b'$M>' in data:
                print("     ↑ MSP HEADER DÉTECTÉ!")
        time.sleep(0.1)

    ser.close()

    print(f"\nTotal: {total_bytes} bytes reçus en 15s")

    if total_bytes == 0:
        print("\n❌ AUCUNE donnée - Le FC n'envoie rien")
        print("\nPossibilités:")
        print("  1. La batterie n'est pas branchée")
        print("  2. Le FC est en mode configuration only")
        print("  3. MSP sur USB est désactivé dans iNAV")
    else:
        print("\n✓ Le FC envoie des données!")

except Exception as e:
    print(f"Erreur: {e}")
