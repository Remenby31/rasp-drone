#!/usr/bin/env python3
"""
Test pour voir si le FC reçoit bien les changements de canaux RC
"""

from inav_drone import INavDrone
import time

print("=" * 60)
print("🔍 TEST LECTURE CANAUX RC")
print("=" * 60)

print("\nDémarrage dans 2 secondes...")
time.sleep(2)

try:
    print("\n[1/4] Connexion...")
    drone = INavDrone("/dev/ttyACM0", baudrate=115200, rc_update_hz=50.0)
    drone.connect()
    time.sleep(1.0)
    print("✓ Connecté")

    print("\n[2/4] Activation RC override...")
    drone.enable_rc_override()
    time.sleep(1.0)
    print("✓ RC override actif")

    print("\n[3/4] Test 1: Tous les canaux au centre/idle...")
    drone.set_rc_override({
        1: 1500,
        2: 1500,
        3: 1000,
        4: 1500,
        5: 1000,  # ARM OFF
    })
    time.sleep(1.0)

    print("\n   Canaux lus par le FC:")
    for i in range(1, 9):
        print(f"   CH{i}: {drone.rc_channels.get(i, 0)} µs")

    print("\n[4/4] Test 2: CH5 à 2000 (ARM)...")
    drone.set_rc_override({5: 2000})
    time.sleep(1.0)

    print("\n   Canaux lus par le FC:")
    for i in range(1, 9):
        val = drone.rc_channels.get(i, 0)
        if i == 5:
            if val >= 1900:
                print(f"   CH{i}: {val} µs ✅ (ARM activé)")
            else:
                print(f"   CH{i}: {val} µs ❌ (devrait être ~2000)")
        else:
            print(f"   CH{i}: {val} µs")

    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC")
    print("=" * 60)

    ch5_value = drone.rc_channels.get(5, 0)

    if ch5_value >= 1900:
        print("\n✅ Le FC reçoit bien CH5=2000")
        print("\nMais le drone ne s'arme pas... Causes possibles:")
        print("  1. Le mode ARM n'est pas lié à CH5 dans l'onglet Modes")
        print("  2. Le range ARM est incorrect")
        print("  3. Autre sécurité bloque (vérifiez onglet Setup)")
        print("\nSOLUTION:")
        print("  → Dans iNAV Configurator > Modes")
        print("  → Supprimez le mode ARM actuel")
        print("  → Recréez-le : Mode ARM, AUX 1 (CH5), range 1700-2100")
    else:
        print(f"\n❌ Problème: Le FC ne reçoit pas CH5=2000 (reçu: {ch5_value})")
        print("\nCauses possibles:")
        print("  1. receiver_type n'est pas MSP")
        print("  2. Bug dans la transmission MSP_SET_RAW_RC")

    drone.disconnect()

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    try:
        drone.disconnect()
    except:
        pass

