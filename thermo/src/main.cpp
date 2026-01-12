#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <Adafruit_MAX31855.h>

// ========== CONFIGURATION ==========
// **IMPORTANT:** Replace these with your actual WiFi credentials
const char *WIFI_SSID = "Casa house";
const char *WIFI_PASSWORD = "12345678";

// MAX31855 Thermocouple Pin Configuration
// Adjust these pin numbers to match your actual wiring
#define MAXCLK 18 // SCK (Clock)
#define MAXDO 19  // MISO (Data Out)
#define MAXCS 5   // CS (Chip Select)

// ========== GLOBAL OBJECTS ==========
Adafruit_MAX31855 thermocouple(MAXCLK, MAXCS, MAXDO);
AsyncWebServer server(80);

// ========== SETUP FUNCTION ==========
void setup()
{
  // Initialize serial communication for debugging
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== ESP32 Thermocouple Server Starting ===");

  // Initialize MAX31855 sensor
  Serial.println("Initializing MAX31855 thermocouple...");
  delay(500);

  // Quick sensor check
  double tempC = thermocouple.readCelsius();
  if (isnan(tempC))
  {
    Serial.println("WARNING: Sensor read failed. Check wiring.");
  }
  else
  {
    Serial.printf("Sensor OK. Current temp: %.1f°C\n", tempC);
  }

  // Connect to WiFi with Static IP
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  // Configure static IP address
  IPAddress local_IP(192, 168, 0, 47); // Your ESP32's IP
  IPAddress gateway(192, 168, 0, 1);   // Your router's IP
  IPAddress subnet(255, 255, 255, 0);  // Subnet mask
  IPAddress primaryDNS(8, 8, 8, 8);    // Google DNS (optional)

  WiFi.mode(WIFI_STA);
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS))
  {
    Serial.println("Static IP configuration failed!");
  }
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // Wait for connection
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.println("\n**WRITE DOWN THIS IP ADDRESS**");
    Serial.print("You can access the temperature at: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/temp");
  }
  else
  {
    Serial.println("\nERROR: WiFi connection failed!");
    Serial.println("Check your SSID and password in the code.");
    return;
  }

  // ========== WEB SERVER ROUTES ==========

  // Root endpoint - helpful info page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request)
            {
    String html = "<html><body>";
    html += "<h1>ESP32 Thermocouple Server</h1>";
    html += "<p>Temperature: <a href='/temp'>/temp</a></p>";
    html += "<p>Diagnostics: <a href='/diagnostics'>/diagnostics</a></p>";
    html += "<p>Current IP: " + WiFi.localIP().toString() + "</p>";
    html += "</body></html>";
    request->send(200, "text/html", html); });

  // Diagnostics endpoint - detailed sensor info
  server.on("/diagnostics", HTTP_GET, [](AsyncWebServerRequest *request)
            {
    double tempC = thermocouple.readCelsius();
    double internalC = thermocouple.readInternal();
    uint8_t errorCode = thermocouple.readError();

    String json = "{";
    json += "\"thermocouple_celsius\":" + String(tempC, 2) + ",";
    json += "\"internal_celsius\":" + String(internalC, 2) + ",";
    json += "\"error_code\":" + String(errorCode) + ",";

    // Decode error bits
    json += "\"errors\":{";
    json += "\"open_circuit\":" + String((errorCode & 0x01) ? "true" : "false") + ",";
    json += "\"short_to_gnd\":" + String((errorCode & 0x02) ? "true" : "false") + ",";
    json += "\"short_to_vcc\":" + String((errorCode & 0x04) ? "true" : "false");
    json += "},";

    json += "\"status\":\"" + String(errorCode == 0 ? "OK" : "FAULT") + "\"";
    json += "}";

    request->send(200, "application/json", json); });

  // Temperature endpoint - returns JSON
  server.on("/temp", HTTP_GET, [](AsyncWebServerRequest *request)
            {
    // Read temperature in Celsius
    double tempC = thermocouple.readCelsius();

    // Check for sensor errors
    if (isnan(tempC)) {
      request->send(500, "application/json", "{\"error\":\"Sensor read failed\"}");
      return;
    }

    // Convert to Fahrenheit
    double tempF = tempC * 9.0 / 5.0 + 32.0;

    // Build JSON response
    String json = "{";
    json += "\"temperature_celsius\":" + String(tempC, 2) + ",";
    json += "\"temperature_fahrenheit\":" + String(tempF, 2);
    json += "}";

    // Send response with CORS headers (allows browser access)
    AsyncWebServerResponse *response = request->beginResponse(200, "application/json", json);
    response->addHeader("Access-Control-Allow-Origin", "*");
    request->send(response); });

  // Start the web server
  server.begin();
  Serial.println("\n=== Web Server Started ===");
  Serial.println("System ready!");
}

// ========== MAIN LOOP ==========
void loop()
{
  // The AsyncWebServer handles requests automatically in the background
  // Nothing needed here
  delay(10); // Small delay to prevent watchdog issues
}
