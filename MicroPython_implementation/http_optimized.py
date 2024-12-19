import socket
import time
import network
import json
from machine import I2C, Pin
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ

# Create the I2C instance and pass that to LSM6DS3
i2c = I2C(0, scl=17, sda=16)
sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)

# Setup Wi-Fi
ssid = 'Galaxy_A15'
password = 'abc123123'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

connection_timeout = 10
while connection_timeout > 0:
    if wlan.status() == 3:  # Connected
        break
    connection_timeout -= 1
    print('Waiting for Wi-Fi connection...')
    time.sleep(1)

if wlan.status() != 3: 
    raise RuntimeError('[ERROR] Failed to establish a network connection')
else: 
    print('[INFO] CONNECTED!')
    network_info = wlan.ifconfig()
    print('[INFO] IP address:', network_info[0])

# Set up socket and listen on port 80
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print('[INFO] Listening on', addr)

# data and activity detection
def get_readings():
    ax, ay, az, gx, gy, gz = sensor.get_readings()
    
    # Simple activity detection logic
    activity = "standing"
    if abs(ax) > 8 or abs(ay) > 8:
        activity = "running"
    elif 4 < abs(ax) <= 8 or 4 < abs(ay) <= 8:
        activity = "walking"
    elif abs(ax) < 2 and abs(ay) < 2 and abs(az) > 8:
        activity = "standing"
    elif abs(az) < 2:
        activity = "falling"
    
    return {
        "ax": ax, "ay": ay, "az": az,
        "gx": gx, "gy": gy, "gz": gz,
        "activity": activity
    }

# Main loop to handle connections
while True:
    cl, addr = s.accept()
    print('[INFO] Client connected from', addr)
    
    request = cl.recv(1024).decode('utf-8')
    print('[INFO] Request:', request)
    
    # Determine requested path
    if "GET /data" in request:
        # Return JSON data
        sensor_data = get_readings()
        response = f"""HTTP/1.1 200 OK
Content-Type: application/json

{json.dumps(sensor_data)}"""
    else:
        # Return the main HTML page
        response = """HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Sensor Values</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 0;
        }
        h1 {
            color: #4CAF50;
            margin-top: 20px;
        }
        .sensor-data {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            max-width: 600px;
            margin: auto;
        }
        .data-item {
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .data-item h2 {
            margin: 0;
        }
        .activity-section {
            margin-top: 30px;
            padding: 20px;
            border: 2px solid #FF5722;
            border-radius: 10px;
            background-color: #fff8f2;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            margin: 30px auto;
        }
        .activity-section h2 {
            margin: 0;
            color: #FF5722;
        }
    </style>
</head>
<body>
    <h1>Live Sensor Values</h1>
    <div class="sensor-data">
        <div class="data-item"><h2>Ax: <span id="ax">0</span></h2></div>
        <div class="data-item"><h2>Ay: <span id="ay">0</span></h2></div>
        <div class="data-item"><h2>Az: <span id="az">0</span></h2></div>
        <div class="data-item"><h2>Gx: <span id="gx">0</span></h2></div>
        <div class="data-item"><h2>Gy: <span id="gy">0</span></h2></div>
        <div class="data-item"><h2>Gz: <span id="gz">0</span></h2></div>
    </div>

    <div class="activity-section">
        <h2>Current Activity: <span id="activity">Unknown</span></h2>
    </div>

    <script>
        async function fetchSensorData() {
            try {
                const response = await fetch('/data');
                const data = await response.json();
                document.getElementById('ax').textContent = data.ax;
                document.getElementById('ay').textContent = data.ay;
                document.getElementById('az').textContent = data.az;
                document.getElementById('gx').textContent = data.gx;
                document.getElementById('gy').textContent = data.gy;
                document.getElementById('gz').textContent = data.gz;
                document.getElementById('activity').textContent = data.activity;

                // Alert if activity is falling
                if (data.activity === "falling") {
                    alert("Alert: Falling detected!");
                }
            } catch (error) {
                console.error('Error fetching sensor data:', error);
            }
        }

        setInterval(fetchSensorData, 1000); // Update every second
    </script>
</body>
</html>
"""
    # Send the response
    cl.send(response.encode('utf-8'))
    cl.close()