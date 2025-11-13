#!/usr/bin/env python3
"""
Envoie une commande MSP simple pour tester la communication bidirectionnelle
"""

import serial
import struct
import time

def send_msp_request(ser, cmd):
    """Envoie une requête MSP et attend la réponse"""
    # Header MSP v1
    header = b'$M<'
    length = 0
    payload = b''

    # Calcul checksum
    checksum = length ^ cmd

    # Frame complète
    frame = header + bytes([length, cmd, checksum])

    print(f"Envoi MSP cmd {cmd}...")
    print(f"  Frame: {' '.join(f'{b:02x}' for b in frame)}")

    ser.write(frame)
    time.sleep(0.1)

    # Lecture réponse
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        print(f"  Réponse ({len(response)} bytes): {' '.join(f'{b:02x}' for b in response)}")
        return response
    else:
        print(f"  Aucune réponse")
        return None

print("=" * 60)
print("TEST COMMUNICATION MSP BIDIRECTIONNELLE")
print("=" * 60)

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    print(f"✓ Port ouvert\n")

    time.sleep(1)

    # Vider le buffer
    if ser.in_waiting > 0:
        junk = ser.read(ser.in_waiting)
        print(f"Buffer initial vidé: {len(junk)} bytes\n")

    # Test avec MSP_API_VERSION (1) - commande simple
    print("Test 1: MSP_API_VERSION (cmd=1)")
    resp = send_msp_request(ser, 1)

    time.sleep(0.2)

    # Test avec MSP_FC_VARIANT (2)
    print("\nTest 2: MSP_FC_VARIANT (cmd=2)")
    resp = send_msp_request(ser, 2)

    time.sleep(0.2)

    # Test avec MSP_ATTITUDE (108)
    print("\nTest 3: MSP_ATTITUDE (cmd=108)")
    resp = send_msp_request(ser, 108)

    ser.close()

    print("\n" + "=" * 60)
    print("\nSi aucune réponse n'a été reçue:")
    print("  → MSP n'est pas actif sur USB")
    print("  → Vérifiez que 'feature VCP' est activé dans la CLI")

except Exception as e:
    print(f"Erreur: {e}")
