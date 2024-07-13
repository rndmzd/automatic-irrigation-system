#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ArduinoOTA.h>
#include "config.h"

const char* wifi_ssid = WIFI_SSID;
const char* wifi_password = WIFI_PASSWORD;
const unsigned long max_open_duration_millis = MAX_OPEN_DURATION_MILLIS;

WebServer server(80);

const int solenoidPin = 2;
bool solenoidState;

unsigned long solenoidOpenTime;

void handlePost() {
  if (server.hasArg("plain") == false) {
    server.send(400, "text/plain", "Body not received");
    return;
  }

  String body = server.arg("plain");
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, body);

  if (error) {
    server.send(400, "text/plain", "Invalid JSON");
    return;
  }

  solenoidState = doc["solenoidState"];
  digitalWrite(solenoidPin, solenoidState ? HIGH : LOW);
  
  if (solenoidState == true) solenoidOpenTime = millis();

  server.send(200, "application/json", "{\"status\":\"success\",\"state\":\"" + String(solenoidState) + "\"}");
}

void reconnectWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconnecting to WiFi...");
    WiFi.disconnect();
    WiFi.begin(wifi_ssid, wifi_password);
    while (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.print(".");
    }
    Serial.println("Reconnected to WiFi");
  }
}

void setupOTA() {
  // Hostname defaults to esp32-[MAC]
  ArduinoOTA.setHostname("esp32-solenoid-controller");

  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else {  // U_SPIFFS
      type = "filesystem";
    }
    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Serial.println("Start updating " + type);
  });

  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });

  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("End Failed");
    }
  });

  ArduinoOTA.begin();
  Serial.println("OTA Ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);

  pinMode(solenoidPin, OUTPUT);
  digitalWrite(solenoidPin, LOW);
  solenoidState = false;

  WiFi.begin(wifi_ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("connected.");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/control", HTTP_POST, handlePost);

  server.begin();
  Serial.println("Server started");

  setupOTA();
}

void loop() {
  server.handleClient();

  if (solenoidState == true) checkShutoff();

  ArduinoOTA.handle();

  reconnectWiFi();
}

void checkShutoff() {
  if (millis() - solenoidOpenTime > max_open_duration_millis) {
    digitalWrite(solenoidPin, LOW);
    solenoidState = false;
  }
}
