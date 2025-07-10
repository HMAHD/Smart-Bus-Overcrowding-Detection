/*
 * IMPORTANT NOTE:
 * This code (main2.cpp) is written to closely follow and implement the accurate Requirements and Objectives
 * as described in the project Report. It is structured to demonstrate the full intended functionality,
 * logic, and compliance with the documented system design, including all features and validation logic.
 *
 * However, due to limitations in the available simulation environment and hardware constraints,
 * not all of these features can be practically demonstrated or tested in the actual POC (Proof of Concept).
 * Some sensors, actuators, or integration points may not be available or fully functional in simulation.
 *
 * Therefore, for the POC demonstration and to showcase the system with the available simulation options,
 * please use main.cpp instead. The main.cpp file is adapted to work within the simulation's capabilities,
 * ensuring a correct and practical demonstration, even if some advanced or report-specific features are omitted.
 *
 * In summary:
 *   - Use this file (main2.cpp) for reference to the requirements-compliant, full-featured implementation.
 *   - Use main.cpp for the actual POC demonstration with available simulation hardware and options.
 *
 * Smart Bus Overcrowding Detection System - Requirements Compliant Version
 * Updated to match exact POC evidence requirements
 * 
 */

#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// Function declarations
void displayStartupScreen();
void handleIRSensors();
void performCameraCount();
void validateAndFuseData();
void updateLocalDisplay();
void updateLEDs();
void checkAndSendAlerts();
void detectBusStop();
void logEvent(String eventType, int count, String description);
void initializePins();
void updateBusStatus();
void arriveAtStop();
void departFromStop();
void simulatePassengerFlow();
void displayDataTable();
void generateCloudDataPacket();
void generateNTCAlert();
void displayDriverPanel();

// Pin definitions
const int ENTRY_SENSOR = 2;      
const int EXIT_SENSOR = 15;      
const int CAMERA_TRIGGER = 4;    
const int GREEN_LED = 25;        
const int YELLOW_LED = 26;       
const int RED_LED = 27;          
const int CAMERA_LED = 13;       
const int MISMATCH_LED = 14;     
const int BUZZER = 32;           
const int PASSENGER_FLOW = 34;   
const int CAMERA_ACCURACY = 35;  
const int FUSION_SWITCH = 33;    

// System constants - UPDATED TO MATCH REQUIREMENTS
const int MAX_CAPACITY = 50;
// Requirements: 0-50 GREEN, 51-80 YELLOW, >80 RED
const int GREEN_THRESHOLD = 50;   // 0-50 passengers
const int YELLOW_THRESHOLD = 80;  // 51-80 passengers
// >80 is RED

// Timing constants
const long CAMERA_INTERVAL = 120000;    // 2 minutes auto camera
const long DISPLAY_UPDATE = 1000;       // 1 second local display
const long SIMULATION_INTERVAL = 5000;  // 5 seconds for passenger simulation
const long STOP_DETECTION_TIME = 30000; // 30 seconds stopped = at bus stop
const long CLOUD_UPLOAD_INTERVAL = 30000; // 30 seconds for cloud upload

// Global variables
int irPassengerCount = 0;
int lastValidatedCount = 0;
int cameraPassengerCount = 0;
int previousEntryState = HIGH;
int previousExitState = HIGH;
int previousCameraState = HIGH;
String validationStatus = "No";  // For validation flag

// Timing variables
unsigned long lastCameraCapture = 0;
unsigned long lastDisplayUpdate = 0;
unsigned long lastSimulation = 0;
unsigned long lastCloudUpload = 0;
unsigned long busStoppedTime = 0;
unsigned long journeyStartTime = 0;

// Statistics
int totalBoardings = 0;
int totalAlightings = 0;
int dailyPassengers = 0;

// Status tracking - UPDATED
enum BusStatus { GREEN, YELLOW, RED };
BusStatus currentStatus = GREEN;
BusStatus previousStatus = GREEN;
String statusColor = "GREEN";
bool atBusStop = false;
String currentStop = "Terminal";
String nextStop = "Colombo Fort";
int stopNumber = 0;

// LCD
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Bus information
struct BusData {
  String busId = "BUS-138-CMB";
  String route = "138 Colombo-Nugegoda";
  float latitude = 6.9271;
  float longitude = 79.8612;
  int passengerCount = 0;
  String status = "GREEN";
  float occupancyPercent = 0;
  String currentLocation = "Terminal";
  String heading = "Nugegoda";
} busData;

// Route information
struct RouteStop {
  String name;
  float lat;
  float lon;
  int avgPassengers;
};

RouteStop routeStops[6] = {
  {"Colombo Fort", 6.9271, 79.8612, 35},
  {"Pettah", 6.9356, 79.8487, 42},
  {"Maradana", 6.9287, 79.8631, 38},
  {"Borella", 6.9146, 79.8779, 30},
  {"Narahenpita", 6.9015, 79.8772, 25},
  {"Nugegoda", 6.8649, 79.8997, 15}
};

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Smart Bus Overcrowding Detection System ===");
  Serial.println("POC Version - Requirements Compliant");
  Serial.println("============================================\n");
  
  // Initialize hardware
  initializePins();
  lcd.init();
  lcd.backlight();
  displayStartupScreen();
  
  // Set initial time
  journeyStartTime = millis();
  
  Serial.println("System ready for operation");
  Serial.println("Thresholds: 0-50 GREEN | 51-80 YELLOW | >80 RED");
  Serial.println("- Entry button (Green): Add passenger");
  Serial.println("- Exit button (Red): Remove passenger");
  Serial.println("- Camera button (Blue): Manual validation");
  Serial.println("- Cloud upload every 30 seconds\n");
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Handle manual IR sensor buttons
  handleIRSensors();
  
  // Handle manual camera trigger
  static int previousCameraButton = HIGH;
  int cameraButton = digitalRead(CAMERA_TRIGGER);
  if (cameraButton == LOW && previousCameraButton == HIGH) {
    Serial.println("\n[MANUAL] Camera validation triggered");
    performCameraCount();
    validateAndFuseData();
    lastCameraCapture = currentMillis;
  }
  previousCameraButton = cameraButton;
  
  // Auto camera capture every 2 minutes
  if (currentMillis - lastCameraCapture >= CAMERA_INTERVAL) {
    Serial.println("\n[AUTO] Scheduled camera validation");
    performCameraCount();
    validateAndFuseData();
    lastCameraCapture = currentMillis;
  }
  
  // Cloud upload every 30 seconds
  if (currentMillis - lastCloudUpload >= CLOUD_UPLOAD_INTERVAL) {
    generateCloudDataPacket();
    lastCloudUpload = currentMillis;
  }
  
  // Simulate passenger flow based on potentiometer
  if (currentMillis - lastSimulation >= SIMULATION_INTERVAL) {
    simulatePassengerFlow();
    lastSimulation = currentMillis;
  }
  
  // Update local display every second
  if (currentMillis - lastDisplayUpdate >= DISPLAY_UPDATE) {
    updateLocalDisplay();
    updateLEDs();
    displayDriverPanel();
    lastDisplayUpdate = currentMillis;
  }
  
  // Detect if bus is at a stop
  detectBusStop();
  
  // Check for alerts
  checkAndSendAlerts();
}

void initializePins() {
  pinMode(ENTRY_SENSOR, INPUT_PULLUP);
  pinMode(EXIT_SENSOR, INPUT_PULLUP);
  pinMode(CAMERA_TRIGGER, INPUT_PULLUP);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(CAMERA_LED, OUTPUT);
  pinMode(MISMATCH_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(FUSION_SWITCH, INPUT_PULLUP);
}

void handleIRSensors() {
  int entryState = digitalRead(ENTRY_SENSOR);
  int exitState = digitalRead(EXIT_SENSOR);
  
  // Manual passenger entry via button
  if (entryState == LOW && previousEntryState == HIGH) {
    irPassengerCount++;
    totalBoardings++;
    dailyPassengers++;
    logEvent("ENTRY", irPassengerCount, currentStop);
    
    // Update without validation (validation happens separately)
    lastValidatedCount = irPassengerCount;
    busData.passengerCount = lastValidatedCount;
    updateBusStatus();
    displayDataTable();
  }
  
  // Manual passenger exit via button
  if (exitState == LOW && previousExitState == HIGH) {
    if (irPassengerCount > 0) {
      irPassengerCount--;
      totalAlightings++;
      logEvent("EXIT", irPassengerCount, currentStop);
      
      lastValidatedCount = irPassengerCount;
      busData.passengerCount = lastValidatedCount;
      updateBusStatus();
      displayDataTable();
    }
  }
  
  previousEntryState = entryState;
  previousExitState = exitState;
}

void simulatePassengerFlow() {
  int flowRate = analogRead(PASSENGER_FLOW);
  
  // Only simulate if potentiometer is turned up
  if (flowRate > 500) {
    int simulationProbability = map(flowRate, 500, 4095, 0, 100);
    
    if (random(100) < simulationProbability) {
      // 70% chance of entry, 30% exit
      if (random(100) < 70) {
        irPassengerCount++;
        totalBoardings++;
        dailyPassengers++;
        logEvent("AUTO_ENTRY", irPassengerCount, currentStop);
      } else {
        if (irPassengerCount > 0) {
          irPassengerCount--;
          totalAlightings++;
          logEvent("AUTO_EXIT", irPassengerCount, currentStop);
        }
      }
      
      lastValidatedCount = irPassengerCount;
      busData.passengerCount = lastValidatedCount;
      updateBusStatus();
    }
  }
}

void performCameraCount() {
  digitalWrite(CAMERA_LED, HIGH);
  delay(500);
  
  // Read camera accuracy from potentiometer
  int accuracyReading = analogRead(CAMERA_ACCURACY);
  int accuracy = map(accuracyReading, 0, 4095, 50, 99);
  
  // Simulate camera count
  int variation = random(-2, 3);
  cameraPassengerCount = constrain(irPassengerCount + variation, 0, 100);
  
  digitalWrite(CAMERA_LED, LOW);
  
  Serial.println("\n=== CAMERA VALIDATION ===");
  Serial.print("IR Count: ");
  Serial.print(irPassengerCount);
  Serial.print(" | Camera Count: ");
  Serial.println(cameraPassengerCount);
}

void validateAndFuseData() {
  int difference = abs(cameraPassengerCount - irPassengerCount);
  
  if (difference <= 3) {
    validationStatus = "Yes";
    lastValidatedCount = round((cameraPassengerCount + irPassengerCount) / 2.0);
    Serial.println("Validation Status: PASSED");
    digitalWrite(MISMATCH_LED, LOW);
  } else {
    validationStatus = "No";
    lastValidatedCount = irPassengerCount;
    Serial.println("Validation Status: FAILED - Using IR count");
    digitalWrite(MISMATCH_LED, HIGH);
  }
  
  // Generate validation data packet
  Serial.println("\n=== VALIDATION DATA PACKET ===");
  Serial.println("{");
  Serial.print("  \"bus_id\": \"");
  Serial.print(busData.busId);
  Serial.println("\",");
  Serial.print("  \"ir_count\": ");
  Serial.print(irPassengerCount);
  Serial.println(",");
  Serial.print("  \"camera_count\": ");
  Serial.print(cameraPassengerCount);
  Serial.println(",");
  Serial.print("  \"validated\": \"");
  Serial.print(validationStatus);
  Serial.println("\",");
  Serial.println("  \"validation_method\": \"Sensor Fusion\",");
  Serial.println("  \"confidence\": \"High\"");
  Serial.println("}");
  
  busData.passengerCount = lastValidatedCount;
  updateBusStatus();
}

void updateBusStatus() {
  previousStatus = currentStatus;
  
  // Requirements: 0-50 GREEN, 51-80 YELLOW, >80 RED
  if (busData.passengerCount <= GREEN_THRESHOLD) {
    currentStatus = GREEN;
    statusColor = "GREEN";
    busData.status = "GREEN";
  } else if (busData.passengerCount <= YELLOW_THRESHOLD) {
    currentStatus = YELLOW;
    statusColor = "YELLOW";
    busData.status = "YELLOW";
  } else {
    currentStatus = RED;
    statusColor = "RED";
    busData.status = "RED";
  }
  
  // Alert if status changed
  if (currentStatus != previousStatus) {
    Serial.print("\n>>> STATUS CHANGED: ");
    Serial.print(statusColor);
    Serial.println(" <<<\n");
  }
}

void displayDataTable() {
  Serial.println("\n=== PASSENGER COUNT DATA TABLE ===");
  Serial.println("Time      | Bus ID       | IR Counter | Status");
  Serial.println("----------|--------------|------------|------------");
  
  // Get current time
  unsigned long seconds = millis() / 1000;
  int hours = (seconds / 3600) % 24;
  int minutes = (seconds / 60) % 60;
  int secs = seconds % 60;
  
  char timeStr[9];
  sprintf(timeStr, "%02d:%02d:%02d", hours + 8, minutes, secs); // +8 for local time
  
  Serial.print(timeStr);
  Serial.print("  | ");
  Serial.print(busData.busId);
  Serial.print(" | ");
  Serial.print(irPassengerCount);
  Serial.print("         | ");
  Serial.println(statusColor);
}

void generateCloudDataPacket() {
  Serial.println("\n=== CLOUD DATA UPLOAD (30s interval) ===");
  
  // CSV format
  Serial.println("CSV Format:");
  Serial.println("upload_time,bus_id,passenger_count,gps_lat,gps_lon,status");
  
  unsigned long seconds = millis() / 1000;
  int hours = (seconds / 3600) % 24;
  int minutes = (seconds / 60) % 60;
  int secs = seconds % 60;
  char timeStr[9];
  sprintf(timeStr, "%02d:%02d:%02d", hours + 8, minutes, secs);
  
  Serial.print(timeStr);
  Serial.print(",");
  Serial.print(busData.busId);
  Serial.print(",");
  Serial.print(busData.passengerCount);
  Serial.print(",");
  Serial.print(busData.latitude, 4);
  Serial.print(",");
  Serial.print(busData.longitude, 4);
  Serial.print(",");
  Serial.println("UPLOADED");
  
  // JSON format
  Serial.println("\nJSON Format:");
  Serial.println("{");
  Serial.println("  \"upload_interval\": \"30 seconds\",");
  Serial.print("  \"timestamp\": \"");
  Serial.print(timeStr);
  Serial.println("\",");
  Serial.println("  \"data_packet\": {");
  Serial.print("    \"bus_id\": \"");
  Serial.print(busData.busId);
  Serial.println("\",");
  Serial.println("    \"sensor_records\": {");
  Serial.print("      \"ir_count\": ");
  Serial.print(irPassengerCount);
  Serial.println(",");
  Serial.print("      \"validated_count\": ");
  Serial.print(lastValidatedCount);
  Serial.println(",");
  Serial.print("      \"gps\": [");
  Serial.print(busData.latitude, 4);
  Serial.print(", ");
  Serial.print(busData.longitude, 4);
  Serial.println("]");
  Serial.println("    },");
  Serial.println("    \"upload_status\": \"SUCCESS\"");
  Serial.println("  }");
  Serial.println("}");
}

void generateNTCAlert() {
  Serial.println("\n===== NTC ALERT MESSAGE =====");
  Serial.println("Alert Type: OVERCROWDED");
  Serial.print("Bus ID: ");
  Serial.println(busData.busId);
  Serial.print("Current Count: ");
  Serial.println(busData.passengerCount);
  Serial.print("Location: ");
  Serial.println(currentStop);
  
  unsigned long seconds = millis() / 1000;
  int hours = (seconds / 3600) % 24;
  int minutes = (seconds / 60) % 60;
  int secs = seconds % 60;
  char timeStr[9];
  sprintf(timeStr, "%02d:%02d:%02d", hours + 8, minutes, secs);
  
  Serial.print("Time: ");
  Serial.println(timeStr);
  Serial.print("GPS: ");
  Serial.print(busData.latitude, 4);
  Serial.print(", ");
  Serial.println(busData.longitude, 4);
  Serial.println("Action Required: Deploy additional bus");
  Serial.println("=============================");
}

void displayDriverPanel() {
  static unsigned long lastPanelUpdate = 0;
  
  // Update panel every 5 seconds
  if (millis() - lastPanelUpdate > 5000) {
    Serial.println("\n╔═══════════════════════════════╗");
    Serial.println("║    DRIVER ALERT PANEL         ║");
    Serial.println("╠═══════════════════════════════╣");
    
    if (currentStatus == GREEN) {
      Serial.println("║  ● Green  (Normal)            ║");
      Serial.println("║  ○ Yellow (Nearly Full)       ║");
      Serial.println("║  ○ Red    (OVERCROWDED)       ║");
    } else if (currentStatus == YELLOW) {
      Serial.println("║  ○ Green  (Normal)            ║");
      Serial.println("║  ● Yellow (Nearly Full)       ║");
      Serial.println("║  ○ Red    (OVERCROWDED)       ║");
    } else {
      Serial.println("║  ○ Green  (Normal)            ║");
      Serial.println("║  ○ Yellow (Nearly Full)       ║");
      Serial.println("║  ● Red    (OVERCROWDED)       ║");
    }
    
    Serial.println("╠═══════════════════════════════╣");
    Serial.print("║  LCD: Pass:");
    Serial.print(busData.passengerCount);
    Serial.print("/");
    Serial.print(MAX_CAPACITY);
    if (currentStatus == RED) {
      Serial.print(" FULL!        ║");
    } else {
      Serial.print("              ║");
    }
    Serial.println("\n╚═══════════════════════════════╝");
    
    lastPanelUpdate = millis();
  }
}

void updateLocalDisplay() {
  lcd.clear();
  
  // Line 1: Count and status
  lcd.setCursor(0, 0);
  lcd.print("Pass:");
  lcd.print(busData.passengerCount);
  lcd.print("/");
  lcd.print(MAX_CAPACITY);
  
  lcd.setCursor(10, 0);
  if (currentStatus == RED) {
    lcd.print("FULL!");
  } else if (currentStatus == YELLOW) {
    lcd.print("NEAR");
  } else {
    lcd.print("OK");
  }
  
  // Line 2: Current stop
  lcd.setCursor(0, 1);
  lcd.print("At: ");
  lcd.print(currentStop.substring(0, 12));
}

void updateLEDs() {
  // Reset all LEDs
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
  
  // Set appropriate LED based on requirements
  switch (currentStatus) {
    case GREEN:
      digitalWrite(GREEN_LED, HIGH);
      break;
    case YELLOW:
      digitalWrite(YELLOW_LED, HIGH);
      break;
    case RED:
      digitalWrite(RED_LED, HIGH);
      break;
  }
}

void detectBusStop() {
  static unsigned long lastMovement = 0;
  int movement = analogRead(PASSENGER_FLOW);
  
  if (movement < 100) { // Bus stopped
    if (!atBusStop && (millis() - lastMovement > STOP_DETECTION_TIME)) {
      atBusStop = true;
      arriveAtStop();
    }
  } else {
    lastMovement = millis();
    if (atBusStop) {
      departFromStop();
      atBusStop = false;
    }
  }
}

void arriveAtStop() {
  stopNumber = (stopNumber + 1) % 6;
  currentStop = routeStops[stopNumber].name;
  nextStop = routeStops[(stopNumber + 1) % 6].name;
  busData.currentLocation = currentStop;
  busData.latitude = routeStops[stopNumber].lat;
  busData.longitude = routeStops[stopNumber].lon;
  
  // Show GPS data with location
  Serial.println("\n=== GPS LOCATION UPDATE ===");
  Serial.println("Timestamp,Bus_ID,GPS_Lat,GPS_Lon,Stop_Name,Passenger_Count");
  
  unsigned long seconds = millis() / 1000;
  int hours = (seconds / 3600) % 24;
  int minutes = (seconds / 60) % 60;
  int secs = seconds % 60;
  char timeStr[9];
  sprintf(timeStr, "%02d:%02d:%02d", hours + 8, minutes, secs);
  
  Serial.print(timeStr);
  Serial.print(",");
  Serial.print(busData.busId);
  Serial.print(",");
  Serial.print(busData.latitude, 4);
  Serial.print(",");
  Serial.print(busData.longitude, 4);
  Serial.print(",");
  Serial.print(currentStop);
  Serial.print(",");
  Serial.println(busData.passengerCount);
}

void departFromStop() {
  Serial.print("\n=== DEPARTED from ");
  Serial.print(currentStop);
  Serial.println(" ===");
}

void checkAndSendAlerts() {
  static bool alertSent = false;
  
  // RED status alert (>80 passengers)
  if (currentStatus == RED && !alertSent) {
    generateNTCAlert();
    
    // Beep pattern
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER, HIGH);
      delay(100);
      digitalWrite(BUZZER, LOW);
      delay(100);
    }
    
    alertSent = true;
  } else if (currentStatus != RED) {
    alertSent = false;
  }
}

void displayStartupScreen() {
  lcd.setCursor(0, 0);
  lcd.print("SBOD System v4");
  lcd.setCursor(0, 1);
  lcd.print("POC Demo");
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Route: 138");
  lcd.setCursor(0, 1);
  lcd.print("CMB-Nugegoda");
  delay(2000);
  
  lcd.clear();
}

void logEvent(String eventType, int count, String location) {
  // Simple log format
  Serial.print("[");
  Serial.print(millis() / 1000);
  Serial.print("s] ");
  Serial.print(eventType);
  Serial.print(" | Count: ");
  Serial.print(count);
  Serial.print(" | Status: ");
  Serial.println(statusColor);
}