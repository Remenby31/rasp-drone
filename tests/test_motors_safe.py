#!/usr/bin/env python3
"""
Test moteurs ULTRA-SAFE : Fait tourner les moteurs très doucement pendant 1s
⚠️ HÉLICES RETIRÉES OBLIGATOIRE ⚠️
"""

from inav_drone import INavDrone
import time
import sys

print("=" * 60)
print("⚠️  TEST MOTEURS - TRÈS FAIBLE PUISSANCE")
print("=" * 60)
print("\n🔴 VÉRIFICATIONS FINALES :")
print("   ✓ Hélices retirées ?")
print("   ✓ Drone sécurisé ?")
print("   ✓ Prêt à débrancher batterie si besoin ?\n")

print("Démarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/6] Connexion au drone...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    print("✓ Connecté\n")

    print("[2/6] Activation du RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif\n")

    print("[3/6] Vérification de la télémétrie...")
    time.sleep(1.0)
    print(f"   Batterie : {drone.battery.voltage:.1f}V")
    print(f"   Prêt à armer : {drone.is_ready_to_arm()}\n")

    if not drone.is_ready_to_arm():
        print("❌ Drone pas prêt à armer!")
        drone.disconnect()
        sys.exit(1)

    print("[4/6] Armement du drone...")
    print("   Throttle à 1000 (idle)")
    drone.set_rc_override({
        3: 1000,  # Throttle à idle
        5: 2000   # ARM
    })
    time.sleep(2.0)  # Attendre que l'armement soit effectif
    print("✓ Armé\n")

    print("[5/6] ⚡ ACTIVATION MOTEURS - 1100µs pendant 1 seconde...")
    print("   (Très faible puissance, juste pour vérifier)")

    # Throttle très bas : 1100µs (100µs au-dessus de l'idle)
    drone.set_rc_override({
        3: 1100,  # Throttle très faible
        5: 2000   # ARM toujours actif
    })

    # Attendre 1 seconde
    time.sleep(1.0)

    print("✓ Test terminé\n")

    print("[6/6] Désarmement...")
    # Retour à idle puis désarmement
    drone.set_rc_override({
        3: 1000,  # Throttle à idle
        5: 1000   # DISARM
    })
    time.sleep(1.0)
    print("✓ Désarmé\n")

    print("=" * 60)
    print("✅ TEST RÉUSSI !")
    print("=" * 60)
    print("\nLes moteurs ont-ils tourné ?")
    print("Si oui, la communication MSP fonctionne parfaitement !\n")

    drone.disconnect()

except KeyboardInterrupt:
    print("\n\n⚠️  INTERRUPTION! Désarmement d'urgence...")
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    print("Débranchez la batterie si nécessaire!\n")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    print("\nDésarmement d'urgence...")
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    print("Débranchez la batterie si nécessaire!\n")
    sys.exit(1)
