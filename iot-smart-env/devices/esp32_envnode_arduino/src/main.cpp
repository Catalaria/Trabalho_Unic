#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

#define WIFI_SSID        "SEU_WIFI_AQUI"
#define WIFI_PASS        "SUA_SENHA_AQUI"

#define MQTT_HOST        "192.168.0.100"
#define MQTT_PORT        1883

#define BASE_TOPIC       "iot/env/room1/reading"
#define NODE_ID          "esp32-envnode-01"
#define FW_VERSION       "esp32-fw-0.1.0"

#define PUBLISH_INTERVAL_MS  2000UL

#define DHTPIN     4
#define DHTTYPE    DHT22
#define PIR_PIN    14
#define SOIL_ADC   34

#define SOIL_DRY_ADC   3000
#define SOIL_WET_ADC   1200

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastPublish = 0;

static float clampf(float v, float lo, float hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

static float soilAdcToPct(int adc) {
  int a = adc;
  if (SOIL_DRY_ADC == SOIL_WET_ADC) return 0.0f;
  float pct = (float)(SOIL_DRY_ADC - a) / (float)(SOIL_DRY_ADC - SOIL_WET_ADC) * 100.0f;
  return clampf(pct, 0.0f, 100.0f);
}

static void ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print(F("[WIFI] Conectando em "));
  Serial.print(WIFI_SSID);
  Serial.println(F(" ..."));

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 20000) {
    delay(250);
    Serial.print('.');
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print(F("[WIFI] OK, IP: "));
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(F("[WIFI] Falha ao conectar."));
  }
}

static void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // (Opcional) Processar comandos no futuro
  Serial.print(F("[MQTT] Msg em "));
  Serial.print(topic);
  Serial.print(F(": "));
  for (unsigned int i = 0; i < length; i++) Serial.print((char)payload[i]);
  Serial.println();
}

static bool mqttConnect() {
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  // LWT (Last Will & Testament)
  String willTopic = String(BASE_TOPIC) + "/status";
  const char* willMsg = "offline";
  bool willRetain = true;
  uint8_t willQos = 1;

  String clientId = String(NODE_ID) + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);

  Serial.print(F("[MQTT] Conectando ao broker... "));
  bool ok = mqttClient.connect(
    clientId.c_str(),
    NULL, NULL,               // user, pass (se necessário, preencha)
    willTopic.c_str(),
    willQos,
    willRetain,
    willMsg
  );

  if (ok) {
    Serial.println(F("OK"));
    // Publica status online (retain)
    mqttClient.publish(willTopic.c_str(), "online", true);
    // (Opcional) subscribe em comandos
    // String cmdTopic = String(BASE_TOPIC) + "/cmd";
    // mqttClient.subscribe(cmdTopic.c_str(), 0);
  } else {
    Serial.print(F("FALHA, rc="));
    Serial.println(mqttClient.state());
  }
  return ok;
}

static void ensureMqtt() {
  if (mqttClient.connected()) return;

  for (int i = 0; i < 3; ++i) {
    if (!mqttClient.connected()) {
      if (mqttConnect()) break;
      delay(1000);
    }
  }
}

static void readSensors(float& tempC, float& humRH, bool& motion, float& soilPct) {
  // DHT
  float t = dht.readTemperature();   // °C
  float h = dht.readHumidity();      // %
  if (isnan(t) || isnan(h)) {
    // Mantém NaN para o JSON excluir campos (opcionalmente, zere)
    tempC = NAN;
    humRH = NAN;
  } else {
    tempC = t;
    humRH = h;
  }

  // PIR
  motion = digitalRead(PIR_PIN) == HIGH;

  // Solo (ADC)
  int adc = analogRead(SOIL_ADC);
  soilPct = soilAdcToPct(adc);
}

static void publishReading() {
  float tempC, humRH, soilPct;
  bool motion;
  readSensors(tempC, humRH, motion, soilPct);

  StaticJsonDocument<320> doc;
  doc["node_id"] = NODE_ID;
  if (!isnan(tempC)) doc["temperature_c"] = tempC;
  if (!isnan(humRH)) doc["humidity_pct"] = humRH;
  doc["soil_moisture_pct"] = soilPct;
  doc["motion"] = motion;
  doc["firmware"] = FW_VERSION;
  doc["rssi_dbm"] = WiFi.RSSI();

  char buf[384];
  size_t n = serializeJson(doc, buf, sizeof(buf));

  if (mqttClient.publish(BASE_TOPIC, (const uint8_t*)buf, n, false)) {
    Serial.print(F("[PUB] "));
    Serial.println(buf);
  } else {
    Serial.println(F("[PUB] Falha ao publicar"));
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);

  pinMode(PIR_PIN, INPUT);
  analogReadResolution(12);

  dht.begin();

  ensureWiFi();
  ensureMqtt();
}

void loop() {
  ensureWiFi();
  ensureMqtt();

  mqttClient.loop(); // trata keepalive/callbacks

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = now;
    publishReading();
  }
}
