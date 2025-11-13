#!/usr/bin/env python3
"""
Test moteurs v2 : Throttle progressif pour initialiser les ESCs
⚠️ HÉLICES RETIRÉES OBLIGATOIRE ⚠️
"""

from inav_drone import INavDrone
import time
import sys

print("=" * 60)
print("⚠️  TEST MOTEURS V2 - Throttle progressif")
print("=" * 60)
print("\n🔴 Hélices retirées ? Drone sécurisé ?\n")

print("Démarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/7] Connexion au drone...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    print("✓ Connecté\n")

    print("[2/7] Activation du RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif\n")

    print("[3/7] Vérification de la télémétrie...")
    time.sleep(1.0)
    print(f"   Batterie : {drone.battery.voltage:.1f}V")
    print(f"   Attitude : Roll={drone.attitude.roll:.1f}° Pitch={drone.attitude.pitch:.1f}°")
    print(f"   Prêt à armer : {drone.is_ready_to_arm()}\n")

    if not drone.is_ready_to_arm():
        print("❌ Drone pas prêt à armer!")
        drone.disconnect()
        sys.exit(1)

    print("[4/7] Configuration initiale - Throttle IDLE...")
    drone.set_rc_override({
        1: 1500,  # Roll centre
        2: 1500,  # Pitch centre
        3: 1000,  # Throttle à idle
        4: 1500,  # Yaw centre
        5: 1000   # DISARM
    })
    time.sleep(0.5)
    print("✓ Canaux RC configurés\n")

    print("[5/7] Armement du drone...")
    drone.set_rc_override({
        5: 2000   # ARM
    })
    time.sleep(3.0)  # Attendre que l'armement soit effectif
    print("✓ Armé\n")

    print("[6/7] ⚡ ACTIVATION MOTEURS - Throttle progressif...")

    # Test 1 : 1050µs pendant 2s
    print("   Test 1: 1050µs pendant 2 secondes...")
    drone.set_rc_override({3: 1050})
    time.sleep(2.0)

    # Test 2 : 1100µs pendant 2s
    print("   Test 2: 1100µs pendant 2 secondes...")
    drone.set_rc_override({3: 1100})
    time.sleep(2.0)

    # Test 3 : 1150µs pendant 2s
    print("   Test 3: 1150µs pendant 2 secondes...")
    drone.set_rc_override({3: 1150})
    time.sleep(2.0)

    # Retour idle
    print("   Retour à idle...")
    drone.set_rc_override({3: 1000})
    time.sleep(1.0)

    print("✓ Tests terminés\n")

    print("[7/7] Désarmement...")
    drone.set_rc_override({5: 1000})
    time.sleep(1.0)
    print("✓ Désarmé\n")

    print("=" * 60)
    print("✅ SCRIPT TERMINÉ")
    print("=" * 60)
    print("\nLes moteurs ont-ils bougé cette fois ?")
    print("Si non, vérifiez:")
    print("  - Les ESCs sont-ils alimentés ?")
    print("  - Les moteurs sont-ils branchés aux ESCs ?")
    print("  - Dans iNAV Configurator > Outputs, PWM est-il activé ?\n")

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
