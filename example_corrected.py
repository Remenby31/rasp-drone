"""
Exemple d'utilisation de INavDrone avec toutes les corrections MSP.

Ce script montre comment utiliser correctement la classe INavDrone avec :
- Activation du RC override (transmission continue MSP_SET_RAW_RC)
- Télémétrie complète (GPS, altitude estimée, attitude)
- Navigation basique
"""

from inav_drone import INavDrone
import time

def main():
    # Connexion au drone
    print("[Exemple] Connexion au drone...")
    drone = INavDrone("/dev/ttyAMA0", baudrate=115200)
    drone.connect()

    # CRITIQUE: Activer le RC override pour contrôler le drone via MSP
    # Cela lance la transmission continue de MSP_SET_RAW_RC à 20Hz
    drone.enable_rc_override()

    # Laisser le temps à la télémétrie d'arriver
    print("[Exemple] Attente de la télémétrie...")
    time.sleep(2.0)

    # Afficher les métriques
    print("\n=== Télémétrie ===")
    print(f"Batterie : {drone.battery.voltage:.1f}V ({drone.battery.mah:.0f} mAh)")
    print(f"Attitude : Roll={drone.attitude.roll:.1f}° Pitch={drone.attitude.pitch:.1f}° Yaw={drone.attitude.yaw:.1f}°")
    print(f"GPS : Lat={drone.gps.lat} Lon={drone.gps.lon}")
    print(f"      Fix={drone.gps.fix_type} Sats={drone.gps.sats} HDOP={drone.gps.hdop:.2f}")
    print(f"      Alt GPS={drone.gps.alt:.1f}m")
    print(f"Altitude estimée FC : {drone.altitude.estimated_alt:.1f}m (vario: {drone.altitude.vario:.1f} cm/s)")

    # Vérifications de sécurité
    if not drone.is_ready_to_arm():
        print("\n[Exemple] Drone pas prêt à armer (batterie faible?)")
        drone.disconnect()
        return

    if drone.gps.fix_type < 3 or drone.gps.sats < 8:
        print(f"\n[Exemple] GPS pas suffisant (fix={drone.gps.fix_type}, sats={drone.gps.sats})")
        print("[Exemple] Recommandé: fix=3 (3D), sats>=8")
        # Pour les tests en intérieur, vous pouvez commenter ce return
        # ATTENTION: Ne volez JAMAIS en extérieur sans bon GPS!
        drone.disconnect()
        return

    print("\n=== Mission de test ===")

    # Mission simple : décollage, montée, hold, atterrissage
    try:
        print("[Exemple] Armement...")
        drone.arm()
        time.sleep(1.0)

        print("[Exemple] Passage en POSHOLD...")
        drone.set_mode("POSHOLD")
        time.sleep(2.0)

        print("[Exemple] Montée à 10m...")
        drone.climb_to(10.0, tol_m=0.5)
        print(f"[Exemple] Altitude atteinte: {drone.altitude.estimated_alt:.1f}m")

        print("[Exemple] Hold 5 secondes...")
        time.sleep(5.0)

        # Navigation vers un point (exemple avec coordonnées proches)
        # IMPORTANT: Remplacez par vos vraies coordonnées!
        if drone.gps.lat and drone.gps.lon:
            target_lat = drone.gps.lat + 0.0001  # ~11m au nord
            target_lon = drone.gps.lon + 0.0001  # ~11m à l'est
            print(f"[Exemple] Navigation vers {target_lat:.7f}, {target_lon:.7f}, 10m...")
            drone.go_to(target_lat, target_lon, 10.0)
            time.sleep(10.0)  # Attendre que le drone se déplace

        print("[Exemple] Retour au home...")
        drone.return_to_home()
        time.sleep(5.0)

        print("[Exemple] Atterrissage...")
        drone.land()

    except KeyboardInterrupt:
        print("\n[Exemple] Interruption! Arrêt d'urgence...")
        drone.emergency_stop()
    except Exception as e:
        print(f"\n[Exemple] Erreur: {e}")
        print("[Exemple] Arrêt d'urgence...")
        drone.emergency_stop()

    # Déconnexion propre
    print("\n[Exemple] Déconnexion...")
    drone.disconnect()
    print("[Exemple] Terminé!")

if __name__ == "__main__":
    main()
