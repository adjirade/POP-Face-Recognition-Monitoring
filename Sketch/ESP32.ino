// ---- Blynk (WAJIB PALING ATAS) ----
#define BLYNK_TEMPLATE_ID "XXX"
#define BLYNK_TEMPLATE_NAME "XXX"
#define BLYNK_AUTH_TOKEN "XXX"

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <DHT.h>

// ---- WiFi ----
char ssid[] = "XXX";
char pass[] = "XXX";

// ---- PIN CONFIG ESP32 ----
#define MQ2_PIN 34
#define FLAME_PIN 5
#define DHT_PIN 14
#define BUZZER_PIN 4

#define DHTTYPE DHT11
DHT dht(DHT_PIN, DHTTYPE);

#define GAS_THRESHOLD 550

void setup() {
  Serial.begin(115200);

  pinMode(FLAME_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  dht.begin();

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);

  Serial.println("ESP32 + MQ2 + Flame + DHT11 + Blynk");
}

void loop() {
  Blynk.run();

  // MQ2
  int gasValue = analogRead(MQ2_PIN);

  // Flame Sensor
  int flameState = digitalRead(FLAME_PIN); // LOW = api terdeteksi

  // DHT11
  float temperature = dht.readTemperature();
  float humidity    = dht.readHumidity();

  // STATUS STRING UNTUK LCD
  String statusGas  = gasValue > GAS_THRESHOLD ? "Gas Tinggi!" : "Gas Aman";
  String statusApi  = (flameState == LOW) ? "Api Terdeteksi!" : "Tidak Ada Api";

  String line1 = "Gas:" + String(gasValue) + " | " + statusGas;
  String line2 = statusApi + " | T:" + String(temperature) + "C H:" + String(humidity) + "%";

  // --- KIRIM KE LCD BLYNK ---
  Blynk.virtualWrite(V0, line1);
  Blynk.virtualWrite(V1, line2);

  // --- KIRIM SUHU & KELEMBAPAN KE VIRTUAL PIN ---
  Blynk.virtualWrite(V2, temperature); // suhu
  Blynk.virtualWrite(V3, humidity);    // kelembapan

  // Alarm
  if (flameState == LOW) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
  } else if (gasValue > GAS_THRESHOLD) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
  }

  delay(500);
}
