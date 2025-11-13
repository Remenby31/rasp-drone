#!/usr/bin/env python3
"""
Test moteurs avec DSHOT - Throttle plus élevé (1400µs)
⚠️ HÉLICES RETIRÉES OBLIGATOIRE ⚠️
"""

from inav_drone import INavDrone
import time
import sys

print("=" * 60)
print("⚠️  TEST MOTEURS - DSHOT300 - Throttle 1400µs")
print("=" * 60)
print("\n🔴 VÉRIFICATIONS:")
print("   ✓ Hélices RETIRÉES ?")
print("   ✓ Drone bien fixé ?")
print("\nDémarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/6] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    print("✓ Connecté")

    print("\n[2/6] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif")

    print("\n[3/6] Armement (throttle idle)...")
    drone.set_rc_override({
        1: 1500,  # Roll
        2: 1500,  # Pitch
        3: 1000,  # Throttle idle
        4: 1500,  # Yaw
        5: 2000   # ARM
    })
    time.sleep(2.0)
    print("✓ Armé")

    print("\n[4/6] 🚀 THROTTLE à 1400µs pendant 2 secondes...")
    print("   (Devrait faire tourner les moteurs avec DSHOT)")
    drone.set_rc_override({3: 1400})

    # Maintenir 2 secondes
    time.sleep(2.0)
    print("✓ Test terminé")

    print("\n[5/6] Retour idle...")
    drone.set_rc_override({3: 1000})
    time.sleep(0.5)

    print("\n[6/6] Désarmement...")
    drone.set_rc_override({5: 1000})
    time.sleep(1.0)
    print("✓ Désarmé")

    print("\n" + "=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)
    print("\n❓ Les moteurs ont-ils tourné cette fois ?")
    print("\nSi NON:")
    print("  → Essaye throttle encore plus haut (1500-1600µs)")
    print("  → Vérifie dans iNAV Configurator > Motors tab")
    print("    si les sliders font tourner les moteurs")

    drone.disconnect()

except KeyboardInterrupt:
    print("\n⚠️  ARRÊT D'URGENCE!")
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    sys.exit(1)
