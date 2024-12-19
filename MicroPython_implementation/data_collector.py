from machine import I2C, Pin
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
import time

def buzz_beep():
    buzz = Pin(18, Pin.OUT)
    i=0
    while i<5:
        print(i)
        if buzz.value()==0:
            buzz.value(1)
            time.sleep(0.1)
        else:
            buzz.value(0)
            time.sleep(0.1)
        i=i+1
    buzz.value(0)

# Create the I2C instance and pass that to LSM6DS3
i2c = I2C(0, scl=17, sda=16)
sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)

time.sleep(3)
buzz_beep()

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
    if timestamp == 60000: 
        break
csv_file.close()
buzz_beep()


