from machine import Pin, I2C
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
import time
import network
import socket
import config


# setup wifi
ssid = config.ssid
password = config.pwd

# connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

connection_timeout = 10
while connection_timeout > 0:
    if wlan.status() == 3: # connected
        break
    connection_timeout -= 1
    print('Waiting for Wi-Fi connection...')
    time.sleep(1)

# check if connection successful
if wlan.status() != 3: 
    raise RuntimeError('[ERROR] Failed to establish a network connection')
else: 
    print('[INFO] CONNECTED!')
    network_info = wlan.ifconfig()
    print('[INFO] IP address:', network_info[0])

# set up socket and listen on port 80
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)  # Listen for incoming connections

print('[INFO] Listening on', addr)

# generate html
def generate_html(ax, ay, az, gx, gy, gz):
    html = f"""\
    HTTP/1.1 200 OK
    Content-Type: text/html

    <!DOCTYPE html>
    <html>
      <head>
          <title>Raspberry Pi Pico Web Server</title>
          <meta http-equiv="refresh" content="2">
      </head>
      <body>
          <h1>Sensing values</h1>
          <h2>t</h2>
          <h3>ax: {ax}</h3>
          <h4>ay: {ay}</h4>
          <h5>az: {az}</h5>
          <h6>gx: {gx}</h6>
          <h7>gy: {gy}</h7>
          <h8>gz: {gz}</h8>
      </body>
    </html>
    """
    return str(html)

i2c = I2C(1, scl=27, sda=26)
sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)

# accept connections + send HTTP response
while True:
    cl, addr = s.accept()
    print('[INFO] Client connected from', addr)
    
    # receive request
    request = cl.recv(1024)
    print('[INFO] Request:', request)
    
    ax, ay, az, gx, gy, gz = sensor.get_readings()
    # generate the response
    response = generate_html(ax, ay, az, gx, gy, gz)
    
    # send the response to the client
    cl.send(response)
    
    # close connection
    cl.close()
