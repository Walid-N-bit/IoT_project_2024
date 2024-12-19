#include "SparkFunLSM6DS3.h"
#include "Wire.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <MicroTFLite.h> 
#include "model.h" 

// Custom I2C pins for Pico W
#define I2C_SDA 16
#define I2C_SCL 17

const float accel_scale = 32768.0/2.0;   // For ±2g
const float gyro_scale = 32768.0 / 250.0;  // For ±250 dps

// IMU setup
LSM6DS3 myIMU(I2C_MODE, 0x6A); // Default constructor for I2C with address 0x6A

// Define Tensor Arena memory for TFLite Micro (adjust size based on model)
constexpr int kTensorArenaSize = 8192;  // Adjust this size based on your model
alignas(16) uint8_t tensor_arena[kTensorArenaSize];

// Input data buffer (modify based on model input shape)
constexpr int kInputLength = 120;  // Assuming 6 input features (e.g., ax, ay, az, gx, gy, gz)
float input_data[kInputLength];

// Output buffer (modify based on model output shape)
float output_data[4];  // Assuming 2 output classes (e.g., "falling", "not falling")

// Wi-Fi Credentials
const char* ssid = "Galaxy_A15";
const char* password = "abc123123";

// Create WebServer object on port 80
WebServer server(80);

// Initialize the model
bool initializeModel() {
  if (!ModelInit(model_data, tensor_arena, kTensorArenaSize)) {
    Serial.println("Model initialization failed!");
    return false;
  }
  Serial.println("Model initialization successful!");
  return true;
}

// Perform inference using the model
void inferActivity() {
  Serial.println("Gathering data for inference...");

  // Gather 50 cycles of sensor data
  for (int frame = 0; frame < 20; frame++) {
        int offset = frame * 6;
        input_data[offset] = myIMU.readFloatAccelX() *accel_scale;
        input_data[offset + 1] = myIMU.readFloatAccelY() * accel_scale;
        input_data[offset + 2] = myIMU.readFloatAccelZ() * accel_scale;
        input_data[offset + 3] = myIMU.readFloatGyroX() * gyro_scale;
        input_data[offset + 4] = myIMU.readFloatGyroY() * gyro_scale;
        input_data[offset + 5] = myIMU.readFloatGyroZ() * gyro_scale;

        delay(10);  // Sample at 10 ms intervals
    }

  // Set the input tensor data using ModelSetInput
  for (int i = 0; i < 120 ; i++) {  // 300 features (50 cycles * 6 features)
    if (!ModelSetInput(input_data[i], i, true)) {
      Serial.println("Failed to set input!");
      return;
    }
  }

  // Run inference
  if (!ModelRunInference()) {
    Serial.println("Inference failed!");
    return;
  }

  // Get the output using ModelGetOutput
  for (int i = 0; i < 4; i++) {  // Assuming 4 output features
    output_data[i] = ModelGetOutput(i);
  }

  // Output the results
  Serial.print("Inference Output: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(output_data[i]);
    Serial.print(" ");
  }
  Serial.println();
}

// Handle "/data" route
void handleDataRequest() {
  // Call the inference function, which also gathers data
  inferActivity();

  // Create a JSON response with the latest data
  DynamicJsonDocument doc(512);
  int lastFrameOffset = (20 - 1) * 6;  // Offset for the last frame in input_data
    doc["ax"] = input_data[lastFrameOffset];
    doc["ay"] = input_data[lastFrameOffset + 1];
    doc["az"] = input_data[lastFrameOffset + 2];
    doc["gx"] = input_data[lastFrameOffset + 3];
    doc["gy"] = input_data[lastFrameOffset + 4];
    doc["gz"] = input_data[lastFrameOffset + 5];

  // Add the output data
  for (int i = 0; i < 4; i++) {
    doc["output"][i] = output_data[i];
  }

    const char* labels[] = {"falling", "running", "sitting", "walking"};
    String activity = "unknown";

    for (int i = 0; i < 4; i++) {
        doc["output"][i] = output_data[i];
        if (output_data[i] >= 0.8) {
            activity = labels[i];
            break; 
        }
    }

   doc["activity"] = activity;

  // Send the JSON response
  String jsonString;
  serializeJson(doc, jsonString);
  server.send(200, "application/json", jsonString);
}


// Serve the HTML page
void handleRootRequest() {
    String html = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Sensor Values</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f9; color: #333; margin: 0; padding: 0; }
        h1 { color: #4CAF50; margin-top: 20px; }
        .sensor-data { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; max-width: 600px; margin: auto; }
        .data-item { padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: white; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
        .data-item h2 { margin: 0; }
        .activity-section { margin-top: 30px; padding: 20px; border: 2px solid #FF5722; border-radius: 10px; background-color: #fff8f2; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); max-width: 400px; margin: 30px auto; }
        .activity-section h2 { margin: 0; color: #FF5722; }
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

                if (data.activity === "falling") {
                    alert("Alert: Falling detected!");
                }
            } catch (error) {
                console.error('Error fetching sensor data:', error);
            }
        }
        setInterval(fetchSensorData, 1000); 
    </script>
</body>
</html>
)rawliteral";
    server.send(200, "text/html", html);
}

void setup() {
    Serial.begin(115200);

    // Initialize I2C with custom pins
    Wire.setSDA(I2C_SDA);
    Wire.setSCL(I2C_SCL);
    Wire.begin();

    // Initialize IMU
    if (myIMU.begin() != 0) {
        Serial.println("Error initializing LSM6DS3 sensor. Check connections!");
        while (1); // Stop if initialization fails
    }

    // Connect to Wi-Fi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to Wi-Fi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\nWi-Fi connected!");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());

    // Initialize the model
    if (!initializeModel()) {
      Serial.println("Model initialization failed, halting.");
      while (true);  // Halt the system
    }   

    // Define server routes
    server.on("/", handleRootRequest);
    server.on("/data", handleDataRequest);

    // Start the server
    server.begin();
    Serial.println("HTTP server started");
}

void loop() {
    server.handleClient();
}
