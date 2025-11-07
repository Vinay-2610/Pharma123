#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#include <SPIFFS.h>
#include <FS.h>

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ======== Wi-Fi Credentials ========
const char* WIFI_SSID = "Babu";
const char* WIFI_PASSWORD = "1234567@";

// ======== Backend API Endpoint ========
const char* SERVER_URL = "http://10.230.115.73:8000/iot/data";

// ======== Configurations ========
const unsigned long SEND_INTERVAL_MS = 300000UL;  // 5 minutes
const int MAX_RETRIES = 3;
unsigned long lastSend = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  dht.begin();

  Serial.println("\n=== ESP32 DHT11 → FastAPI (PharmaChain) + Offline SPIFFS ===");

  if (!SPIFFS.begin(true)) {
    Serial.println("❌ SPIFFS mount failed! Check flash memory.");
  } else {
    Serial.println("✅ SPIFFS mounted successfully.");
  }

  connectWiFi();
  lastSend = millis() - SEND_INTERVAL_MS;
}

void loop() {
  maintainWiFiConnection();

  unsigned long now = millis();
  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;
    sendSensorData();
  } else {
    unsigned long remaining = (SEND_INTERVAL_MS - (now - lastSend)) / 1000;
    static unsigned long lastCountdownPrint = 0;
    if (millis() - lastCountdownPrint >= 10000) {
      lastCountdownPrint = millis();
      Serial.print("⏳ Next reading in ");
      Serial.print(remaining);
      Serial.println(" seconds...");
    }
  }

  delay(100);
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int retries = 0;

  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(1000);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ Connected to WiFi!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    uploadStoredData();  // Upload previously failed data
  } else {
    Serial.println("\n❌ WiFi connection failed.");
  }
}

void maintainWiFiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi lost. Attempting reconnection...");
    WiFi.disconnect();
    WiFi.reconnect();

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 15) {
      delay(1000);
      Serial.print(".");
      attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n✅ Reconnected to WiFi!");
      uploadStoredData();  // Try uploading any saved data
    } else {
      Serial.println("\n❌ Failed to reconnect WiFi.");
    }
  }
}

void sendSensorData() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("⚠️ Failed to read from DHT sensor!");
    return;
  }

  String payload = "{\"batch_id\":\"BATCH001\",";
  payload += "\"temperature\":" + String(temperature, 2) + ",";
  payload += "\"humidity\":" + String(humidity, 2) + ",";
  payload += "\"location\":\"Auto-Detected\",";
  payload += "\"sensor_id\":\"ESP32_SENSOR_01\"}";

  Serial.println();
  Serial.print("🌡 Temperature: ");
  Serial.print(temperature);
  Serial.print(" °C  |  💧 Humidity: ");
  Serial.print(humidity);
  Serial.println(" %");

  Serial.print("POSTing to: ");
  Serial.println(SERVER_URL);

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ No WiFi — storing data locally.");
    storeDataLocally(payload);
    return;
  }

  bool success = false;
  for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    HTTPClient http;
    http.setTimeout(8000);
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(payload);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.print("✅ [Attempt ");
      Serial.print(attempt);
      Serial.println("] Data sent successfully!");
      Serial.println(response);
      success = true;
      http.end();
      break;
    } else {
      Serial.print("❌ [Attempt ");
      Serial.print(attempt);
      Serial.print("] Send failed (Code: ");
      Serial.print(httpResponseCode);
      Serial.println("). Retrying in 5s...");
      http.end();
      delay(5000);
    }
  }

  if (!success) {
    Serial.println("🚨 Failed to send after retries — storing offline.");
    storeDataLocally(payload);
  } else {
    Serial.println("⏳ Waiting 5 minutes before next reading...");
  }
}

void storeDataLocally(String data) {
  File file = SPIFFS.open("/failed_data.json", FILE_APPEND);
  if (!file) {
    Serial.println("❌ Failed to open file for writing.");
    return;
  }
  file.println(data);
  file.close();
  Serial.println("💾 Data stored locally in /failed_data.json");
}

void uploadStoredData() {
  File file = SPIFFS.open("/failed_data.json", FILE_READ);
  if (!file || file.size() == 0) {
    Serial.println("📭 No offline data to upload.");
    file.close();
    return;
  }

  Serial.println("📤 Uploading stored offline data...");
  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) continue;

    HTTPClient http;
    http.setTimeout(8000);
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(line);
    if (code > 0) {
      Serial.print("✅ Uploaded offline record, code ");
      Serial.println(code);
    } else {
      Serial.print("❌ Failed to upload offline record, code ");
      Serial.println(code);
      http.end();
      break;  // Stop trying, keep remaining data
    }
    http.end();
    delay(2000);
  }
  file.close();

  // Clear file after successful upload
  SPIFFS.remove("/failed_data.json");
  Serial.println("🧹 Cleared offline data after upload.");
}
