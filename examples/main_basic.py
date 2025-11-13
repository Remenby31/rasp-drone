from inav_drone import INavDrone
import time

drone = INavDrone("/dev/ttyAMA0", 115200)
drone.connect()

time.sleep(1.0)  # laisse le temps à la télémétrie d'arriver
print("VOLTS:", drone.battery.voltage)
print("GPS:", drone.gps)

if drone.is_ready_to_arm():
    drone.arm()
    drone.set_mode("POSHOLD")
    drone.climb_to(50)  # monte vers 50 m
    drone.go_to(48.1234567, 2.1234567, 50)
    drone.return_to_home()
    drone.disarm()

drone.disconnect()
