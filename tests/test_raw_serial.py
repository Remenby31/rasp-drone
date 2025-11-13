#!/usr/bin/env python3
"""
Test brut du port série - affiche toutes les données reçues
Permet de vérifier si QUELQUE CHOSE arrive du FC
"""

import serial
import time
import sys

def main():
    print("=" * 60)
    print("TEST BRUT DU PORT SÉRIE")
    print("=" * 60)
    print("\nCe script affiche toutes les données brutes reçues.")
    print("Si MSP est actif, vous devriez voir des caractères s'afficher.\n")

    try:
        ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
        print(f"✓ Port /dev/ttyAMA0 ouvert @ 115200 bauds\n")
        print("Écoute pendant 10 secondes...")
        print("(Appuyez Ctrl+C pour arrêter)\n")
        print("-" * 60)

        start_time = time.time()
        byte_count = 0

        while (time.time() - start_time) < 10:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                byte_count += len(data)
                # Afficher en hexadécimal
                hex_str = ' '.join(f'{b:02x}' for b in data)
                print(f"RX [{len(data)} bytes]: {hex_str}")

                # Chercher le header MSP '$M<' ou '$M>'
                if b'$M' in data:
                    print("  ↑ HEADER MSP DÉTECTÉ! ✓")

        print("-" * 60)
        print(f"\nTotal reçu : {byte_count} bytes en 10 secondes")

        if byte_count == 0:
            print("\n❌ AUCUNE DONNÉE REÇUE!")
            print("\nCauses possibles:")
            print("  1. UART6 n'est pas configuré pour MSP dans iNAV")
            print("  2. TX/RX inversés (essayez de les croiser)")
            print("  3. Le FC n'est pas alimenté")
            print("  4. Mauvais baudrate (essayez 57600 ou 9600)")
        elif b'$M' not in data:
            print("\n⚠️  Des données arrivent mais pas de protocol MSP détecté")
            print("     Vérifiez que MSP est activé sur UART6 dans iNAV")
        else:
            print("\n✓ Communication MSP active!")

        ser.close()

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur\n")
        sys.exit(0)
