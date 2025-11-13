#!/usr/bin/env python3
"""
Détecte automatiquement le port série du contrôleur de vol
"""

import serial.tools.list_ports
import sys

print("=" * 60)
print("DÉTECTION DES PORTS SÉRIE")
print("=" * 60)

ports = serial.tools.list_ports.comports()

if not ports:
    print("\n❌ Aucun port série détecté!")
    print("\nVérifiez:")
    print("  - Le FC est branché en USB")
    print("  - Le FC est alimenté")
    sys.exit(1)

print(f"\n✓ {len(ports)} port(s) détecté(s):\n")

fc_candidates = []

for i, port in enumerate(ports, 1):
    print(f"{i}. {port.device}")
    print(f"   Description : {port.description}")
    print(f"   Fabricant   : {port.manufacturer if port.manufacturer else 'N/A'}")

    # Identifier les candidats probables pour FC
    if 'ACM' in port.device or 'USB' in port.device:
        fc_candidates.append(port.device)
        if 'STM' in str(port.description).upper() or 'Serial' in port.description:
            print(f"   → 🎯 PROBABLEMENT LE FC!")
    print()

print("=" * 60)

if fc_candidates:
    print(f"\n✓ Port(s) probable(s) pour le FC: {', '.join(fc_candidates)}")
    print(f"\nUtilisez ce port dans le code:")
    print(f"   drone = INavDrone('{fc_candidates[0]}', baudrate=115200)")
else:
    print("\n⚠️  Aucun port USB/ACM détecté")
    print("    Si le FC est en UART, utilisez /dev/ttyAMA0")
