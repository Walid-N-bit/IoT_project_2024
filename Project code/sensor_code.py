from machine import I2C
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
import time

# Create the I2C instance and pass that to LSM6DS3
i2c = I2C(1, scl=27, sda=26)
sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)

#print("ax, ay, az, gx, gy, gz")

timestamp = 0
csv_file = open("data.csv", 'a')
csv_file.write("timestamp, ax, ay, az, gx, gy, gz\n")
# Grab and print the current readings once per second
while True:
    
    ax, ay, az, gx, gy, gz = sensor.get_readings()
    print("{}, {}, {}, {}, {}, {}, {}".format(timestamp, ax, ay, az, gx, gy, gz))
    csv_file.write(f"{timestamp}, {ax}, {ay}, {az}, {gx}, {gy}, {gz}\n")
    timestamp = timestamp + 10 
    time.sleep(0.01)
    if timestamp == 5000: 
        break
csv_file.close()

