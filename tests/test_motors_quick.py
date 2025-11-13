#!/usr/bin/env python3
"""
Test moteurs rapide : 1200µs pendant 1 seconde
⚠️ HÉLICES RETIRÉES OBLIGATOIRE ⚠️
"""

from inav_drone import INavDrone
import time
import sys

print("=" * 60)
print("⚠️  TEST MOTEURS - 1200µs pendant 1s")
print("=" * 60)

print("\nDémarrage dans 3 secondes...")
time.sleep(3)

try:
    print("\n[1/5] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    print("✓ Connecté")

    print("\n[2/5] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif")

    print("\n[3/5] Armement...")
    drone.set_rc_override({
        1: 1500,  # Roll
        2: 1500,  # Pitch
        3: 1000,  # Throttle idle
        4: 1500,  # Yaw
        5: 2000   # ARM
    })
    time.sleep(2.0)
    print("✓ Armé")

    print("\n[4/5] ⚡ ACTIVATION MOTEURS - 1200µs pendant 1 seconde...")
    drone.set_rc_override({3: 1200})
    time.sleep(1.0)
    print("✓ Test terminé")

    # Retour idle
    drone.set_rc_override({3: 1000})
    time.sleep(0.5)

    print("\n[5/5] Désarmement...")
    drone.set_rc_override({5: 1000})
    time.sleep(1.0)
    print("✓ Désarmé")

    print("\n" + "=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)
    print("\nMoteurs bougés ? Si non:")
    print("  → Vérifiez que PWM est activé dans iNAV (Outputs tab)")
    print("  → ESCs alimentés et connectés ?")

    drone.disconnect()

except KeyboardInterrupt:
    print("\n⚠️  INTERRUPTION!")
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    try:
        drone.emergency_stop()
        drone.disconnect()
    except:
        pass
    sys.exit(1)
