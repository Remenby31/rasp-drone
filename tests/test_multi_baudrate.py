#!/usr/bin/env python3
"""
Test avec plusieurs baudrates pour détecter une éventuelle communication
"""

import serial
import time

baudrates = [9600, 19200, 38400, 57600, 115200, 230400]

print("=" * 60)
print("TEST MULTI-BAUDRATE")
print("=" * 60)
print("\nTest de communication sur /dev/ttyAMA0 avec différents baudrates\n")

for baud in baudrates:
    print(f"Test @ {baud} bauds... ", end='', flush=True)
    try:
        ser = serial.Serial('/dev/ttyAMA0', baud, timeout=0.5)
        time.sleep(0.5)

        byte_count = 0
        for _ in range(5):  # 5 tentatives de 0.2s
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                byte_count += len(data)
            time.sleep(0.2)

        ser.close()

        if byte_count > 0:
            print(f"✓ {byte_count} bytes reçus!")
        else:
            print("aucune donnée")

    except Exception as e:
        print(f"erreur: {e}")

print("\n" + "=" * 60)
print("\nSi aucun baudrate ne fonctionne:")
print("  → Le FC n'envoie rien sur ce port UART")
print("  → Vérifiez le câblage physique (TX/RX/GND)")
print("  → Essayez un autre port UART (ex: UART1)")
