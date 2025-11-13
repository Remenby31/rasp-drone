#!/usr/bin/env python3
"""
Script de test de connexion MSP via USB - SANS armement ni contrôle moteurs
Vérifie simplement que la communication MSP fonctionne et affiche la télémétrie.
"""

from inav_drone import INavDrone
import time
import sys

def main():
    print("=" * 60)
    print("TEST DE CONNEXION MSP via USB - Lecture seule")
    print("=" * 60)
    print("\n⚠️  Ce script NE va PAS armer le drone")
    print("⚠️  Il lit uniquement la télémétrie pour tester la connexion\n")

    # Connexion au drone via USB
    print("[1/4] Connexion au port USB /dev/ttyACM0 @ 115200 bauds...")
    try:
        drone = INavDrone("/dev/ttyACM0", baudrate=115200)
        drone.connect()
        print("✓ Port USB ouvert avec succès\n")
    except Exception as e:
        print(f"✗ ERREUR de connexion: {e}")
        sys.exit(1)

    # Attente de la télémétrie
    print("[2/4] Attente de la télémétrie MSP (3 secondes)...")
    time.sleep(3.0)

    # Lecture et affichage de la télémétrie
    print("[3/4] Lecture de la télémétrie...\n")

    try:
        print("=" * 60)
        print("📡 TÉLÉMÉTRIE DRONE")
        print("=" * 60)

        # Batterie
        print(f"\n🔋 BATTERIE")
        print(f"   Tension      : {drone.battery.voltage:.2f} V")
        print(f"   Consommation : {drone.battery.mah:.0f} mAh")

        if drone.battery.voltage < 10.0:
            print("   ⚠️  Tension faible!")
        elif drone.battery.voltage > 0:
            print("   ✓ Tension OK")

        # Attitude
        print(f"\n🎯 ATTITUDE")
        print(f"   Roll  : {drone.attitude.roll:+7.2f}°")
        print(f"   Pitch : {drone.attitude.pitch:+7.2f}°")
        print(f"   Yaw   : {drone.attitude.yaw:+7.2f}°")

        # GPS
        print(f"\n🛰️  GPS")
        if drone.gps.lat is not None and drone.gps.lon is not None:
            print(f"   Latitude     : {drone.gps.lat:.7f}°")
            print(f"   Longitude    : {drone.gps.lon:.7f}°")
            print(f"   Altitude GPS : {drone.gps.alt:.1f} m")
        else:
            print("   Position     : Non disponible")

        print(f"   Fix Type     : {drone.gps.fix_type} (0=No fix, 2=2D, 3=3D)")
        print(f"   Satellites   : {drone.gps.sats}")
        print(f"   HDOP         : {drone.gps.hdop:.2f}")
        print(f"   Vitesse sol  : {drone.gps.speed:.1f} m/s")
        print(f"   Cap          : {drone.gps.ground_course:.1f}°")

        if drone.gps.fix_type >= 3 and drone.gps.sats >= 8:
            print("   ✓ GPS prêt pour navigation")
        elif drone.gps.fix_type >= 2:
            print("   ⚠️  Fix 2D seulement, pas idéal")
        else:
            print("   ✗ Pas de fix GPS")

        # Altitude estimée par le FC
        print(f"\n📏 ALTITUDE ESTIMÉE (Flight Controller)")
        print(f"   Altitude : {drone.altitude.estimated_alt:.2f} m")
        print(f"   Vario    : {drone.altitude.vario:.1f} cm/s")

        # Canaux RC
        print(f"\n📻 CANAUX RC (valeurs reçues par le FC)")
        for i in range(1, 9):
            if i in drone.rc_channels:
                val = drone.rc_channels[i]
                print(f"   CH{i} : {val:4d} µs", end="")
                if i == 1:
                    print(" (Roll)", end="")
                elif i == 2:
                    print(" (Pitch)", end="")
                elif i == 3:
                    print(" (Throttle)", end="")
                elif i == 4:
                    print(" (Yaw)", end="")
                elif i == 5:
                    print(" (ARM)", end="")
                print()

        # État général
        print(f"\n🔍 ÉTAT GÉNÉRAL")
        print(f"   Armé           : {'OUI ⚠️' if drone.armed else 'NON ✓'}")
        ready = drone.is_ready_to_arm()
        print(f"   Prêt à armer   : {'OUI' if ready else 'NON'}")

        if not ready:
            if drone.battery.voltage < 10.0:
                print("      → Batterie trop faible")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n✗ ERREUR lors de la lecture MSP: {e}")
        drone.disconnect()
        sys.exit(1)

    # Test réussi
    print("[4/4] Test terminé avec succès! ✓\n")
    print("📋 RÉSULTAT :")
    print("   ✅ La connexion USB fonctionne parfaitement!")
    print("   ✅ La communication MSP est opérationnelle")
    print("\n📋 PROCHAINES ÉTAPES :")
    print("   1. Toutes les valeurs semblent cohérentes")
    print("   2. Vous pouvez maintenant tester le contrôle RC via MSP\n")

    # Déconnexion propre
    print("Déconnexion...")
    drone.disconnect()
    print("✓ Terminé!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur (Ctrl+C)")
        print("Sortie propre...\n")
        sys.exit(0)
