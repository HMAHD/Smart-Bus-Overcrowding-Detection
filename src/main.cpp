/*
 * Smart Bus Overcrowding Detection System - Wokwi Demo Version
 * Simplified for demonstration without external server dependencies
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

// System constants
const int MAX_CAPACITY = 50;
const float NORMAL_THRESHOLD = 0.4;   // <40% is undercrowded
const float YELLOW_THRESHOLD = 0.6;   // 60% nearly full
const float RED_THRESHOLD = 0.8;      // 80% overcrowded

// Timing constants
const long CAMERA_INTERVAL = 120000;    // 2 minutes auto camera
const long DISPLAY_UPDATE = 1000;       // 1 second local display
const long SIMULATION_INTERVAL = 5000;  // 5 seconds for passenger simulation
const long STOP_DETECTION_TIME = 30000; // 30 seconds stopped = at bus stop

// Global variables
int irPassengerCount = 0;
int lastValidatedCount = 0;
int cameraPassengerCount = 0;
int previousEntryState = HIGH;
int previousExitState = HIGH;
int previousCameraState = HIGH;

// Timing variables
unsigned long lastCameraCapture = 0;
unsigned long lastDisplayUpdate = 0;
unsigned long lastSimulation = 0;
unsigned long busStoppedTime = 0;
unsigned long journeyStartTime = 0;

// Statistics
int totalBoardings = 0;
int totalAlightings = 0;
int dailyPassengers = 0;

// Status tracking
enum BusStatus { NORMAL, NEARLY_FULL, OVERCROWDED, UNDERCROWDED };
BusStatus currentStatus = NORMAL;
BusStatus previousStatus = NORMAL;
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
  String status = "NORMAL";
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
  Serial.println("\n=== Smart Bus System - Akash Hasendra ===");
  Serial.println("Version 3.0 - Demonstration");
  Serial.println("====================================\n");
  
  // Initialize hardware
  initializePins();
  lcd.init();
  lcd.backlight();
  displayStartupScreen();
  
  // Set initial time
  journeyStartTime = millis();
  
  Serial.println("System ready for operation");
  Serial.println("- Entry button (Green): Add passenger");
  Serial.println("- Exit button (Red): Remove passenger");
  Serial.println("- Camera button (Blue): Manual camera capture");
  Serial.println("- Flow potentiometer: Simulation speed");
  Serial.println("- Accuracy potentiometer: Camera accuracy");
  Serial.println("- Fusion switch: Enable/disable sensor fusion\n");
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Handle manual IR sensor buttons
  handleIRSensors();
  
  // Handle manual camera trigger
  static int previousCameraButton = HIGH;
  int cameraButton = digitalRead(CAMERA_TRIGGER);
  if (cameraButton == LOW && previousCameraButton == HIGH) {
    Serial.println("\n[MANUAL] Camera triggered by button");
    performCameraCount();
    validateAndFuseData();
    lastCameraCapture = currentMillis;
  }
  previousCameraButton = cameraButton;
  
  // Auto camera capture every 2 minutes
  if (currentMillis - lastCameraCapture >= CAMERA_INTERVAL) {
    Serial.println("\n[AUTO] Scheduled camera capture");
    performCameraCount();
    validateAndFuseData();
    lastCameraCapture = currentMillis;
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
    if (irPassengerCount < MAX_CAPACITY) {
      irPassengerCount++;
      totalBoardings++;
      dailyPassengers++;
      logEvent("MANUAL ENTRY", irPassengerCount, currentStop);
      
      // If fusion is disabled, update directly
      if (digitalRead(FUSION_SWITCH) == LOW) {
        lastValidatedCount = irPassengerCount;
        busData.passengerCount = lastValidatedCount;
        busData.occupancyPercent = (float)lastValidatedCount / MAX_CAPACITY * 100;
        updateBusStatus();
      }
    } else {
      Serial.println("BUS FULL - Entry denied!");
      digitalWrite(BUZZER, HIGH);
      delay(500);
      digitalWrite(BUZZER, LOW);
    }
  }
  
  // Manual passenger exit via button
  if (exitState == LOW && previousExitState == HIGH) {
    if (irPassengerCount > 0) {
      irPassengerCount--;
      totalAlightings++;
      logEvent("MANUAL EXIT", irPassengerCount, currentStop);
      
      // If fusion is disabled, update directly
      if (digitalRead(FUSION_SWITCH) == LOW) {
        lastValidatedCount = irPassengerCount;
        busData.passengerCount = lastValidatedCount;
        busData.occupancyPercent = (float)lastValidatedCount / MAX_CAPACITY * 100;
        updateBusStatus();
      }
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
        if (irPassengerCount < MAX_CAPACITY) {
          irPassengerCount++;
          totalBoardings++;
          dailyPassengers++;
          logEvent("AUTO ENTRY", irPassengerCount, currentStop);
        }
      } else {
        if (irPassengerCount > 0) {
          irPassengerCount--;
          totalAlightings++;
          logEvent("AUTO EXIT", irPassengerCount, currentStop);
        }
      }
      
      // Update if fusion is disabled
      if (digitalRead(FUSION_SWITCH) == LOW) {
        lastValidatedCount = irPassengerCount;
        busData.passengerCount = lastValidatedCount;
        busData.occupancyPercent = (float)lastValidatedCount / MAX_CAPACITY * 100;
        updateBusStatus();
      }
    }
  }
}

void performCameraCount() {
  Serial.println("\n[CAMERA CAPTURE]");
  digitalWrite(CAMERA_LED, HIGH);
  
  // Simulate camera processing
  delay(500);
  
  // Read camera accuracy from potentiometer
  int accuracyReading = analogRead(CAMERA_ACCURACY);
  int accuracy = map(accuracyReading, 0, 4095, 50, 99);
  
  // Simulate camera count with variations based on accuracy
  float occupancyRatio = (float)irPassengerCount / MAX_CAPACITY;
  int maxVariation = map(accuracy, 50, 99, 5, 1);
  int variation;
  
  if (occupancyRatio > 0.8) {
    // Crowded - camera might see more
    variation = random(-1, maxVariation + 2);
  } else if (occupancyRatio > 0.5) {
    // Moderate
    variation = random(-maxVariation/2, maxVariation);
  } else {
    // Light - more accurate
    variation = random(0, maxVariation/2 + 1);
  }
  
  cameraPassengerCount = constrain(irPassengerCount + variation, 0, MAX_CAPACITY + 3);
  
  digitalWrite(CAMERA_LED, LOW);
  
  Serial.print("Camera Count: ");
  Serial.print(cameraPassengerCount);
  Serial.print(" | IR Count: ");
  Serial.print(irPassengerCount);
  Serial.print(" | Accuracy: ");
  Serial.print(accuracy);
  Serial.println("%");
}

void validateAndFuseData() {
  // Check if fusion is enabled
  if (digitalRead(FUSION_SWITCH) == LOW) {
    Serial.println("Sensor fusion DISABLED - using IR count only");
    lastValidatedCount = irPassengerCount;
    digitalWrite(MISMATCH_LED, LOW);
  } else {
    Serial.println("Sensor fusion ENABLED");
    
    int previousCount = lastValidatedCount;
    int difference = abs(cameraPassengerCount - irPassengerCount);
    
    if (difference <= 2) {
      // Sensors agree
      lastValidatedCount = round(0.7 * cameraPassengerCount + 0.3 * irPassengerCount);
      digitalWrite(MISMATCH_LED, LOW);
      Serial.println("Sensors AGREE ✓");
    } else if (difference <= 5) {
      // Small mismatch
      float cameraWeight = 0.6;
      if (irPassengerCount > 40) cameraWeight = 0.8;
      lastValidatedCount = round(cameraWeight * cameraPassengerCount + (1 - cameraWeight) * irPassengerCount);
      digitalWrite(MISMATCH_LED, HIGH);
      Serial.println("Small mismatch detected ⚠");
    } else {
      // Large mismatch
      Serial.println("LARGE MISMATCH DETECTED ⚠⚠");
      if (irPassengerCount > 30) {
        lastValidatedCount = cameraPassengerCount;
      } else {
        lastValidatedCount = irPassengerCount;
      }
      digitalWrite(MISMATCH_LED, HIGH);
    }
  }
  
  lastValidatedCount = constrain(lastValidatedCount, 0, MAX_CAPACITY);
  
  // Update bus data
  busData.passengerCount = lastValidatedCount;
  busData.occupancyPercent = (float)lastValidatedCount / MAX_CAPACITY * 100;
  
  // Update status
  updateBusStatus();
  
  Serial.print("VALIDATED COUNT: ");
  Serial.print(lastValidatedCount);
  Serial.print(" (");
  Serial.print(busData.occupancyPercent);
  Serial.println("%)");
}

void updateBusStatus() {
  previousStatus = currentStatus;
  
  if (busData.occupancyPercent < NORMAL_THRESHOLD * 100) {
    currentStatus = UNDERCROWDED;
    busData.status = "UNDERCROWDED";
  } else if (busData.occupancyPercent < YELLOW_THRESHOLD * 100) {
    currentStatus = NORMAL;
    busData.status = "NORMAL";
  } else if (busData.occupancyPercent < RED_THRESHOLD * 100) {
    currentStatus = NEARLY_FULL;
    busData.status = "NEARLY_FULL";
  } else {
    currentStatus = OVERCROWDED;
    busData.status = "OVERCROWDED";
  }
  
  // Alert if status changed
  if (currentStatus != previousStatus) {
    Serial.print("\n>>> STATUS CHANGED: ");
    Serial.print(busData.status);
    Serial.println(" <<<\n");
  }
}

void updateLocalDisplay() {
  lcd.clear();
  
  // Line 1: Count and status
  lcd.setCursor(0, 0);
  lcd.print("Pass:");
  lcd.print(lastValidatedCount);
  lcd.print("/");
  lcd.print(MAX_CAPACITY);
  
  lcd.setCursor(10, 0);
  if (currentStatus == OVERCROWDED) {
    lcd.print("FULL!");
  } else if (currentStatus == NEARLY_FULL) {
    lcd.print("NEAR");
  } else if (currentStatus == UNDERCROWDED) {
    lcd.print("LOW");
  } else {
    lcd.print("OK");
  }
  
  // Line 2: Current stop or stats
  lcd.setCursor(0, 1);
  if (atBusStop) {
    lcd.print("At: ");
    lcd.print(currentStop.substring(0, 12));
  } else {
    lcd.print("Today: ");
    lcd.print(dailyPassengers);
    lcd.print(" pass");
  }
}

void updateLEDs() {
  // Reset all LEDs
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
  
  // Set appropriate LED
  switch (currentStatus) {
    case UNDERCROWDED:
    case NORMAL:
      digitalWrite(GREEN_LED, HIGH);
      break;
    case NEARLY_FULL:
      digitalWrite(YELLOW_LED, HIGH);
      break;
    case OVERCROWDED:
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
  
  Serial.print("\n=== ARRIVED at ");
  Serial.print(currentStop);
  Serial.println(" ===");
  Serial.print("Next stop: ");
  Serial.println(nextStop);
}

void departFromStop() {
  Serial.print("\n=== DEPARTED from ");
  Serial.print(currentStop);
  Serial.println(" ===");
  Serial.print("Boarded: ");
  Serial.print(totalBoardings);
  Serial.print(" | Alighted: ");
  Serial.println(totalAlightings);
  
  // Reset stop statistics
  totalBoardings = 0;
  totalAlightings = 0;
}

void checkAndSendAlerts() {
  static bool alertSent = false;
  
  // Overcrowding alert
  if (currentStatus == OVERCROWDED && !alertSent) {
    Serial.println("\n!!! OVERCROWDING ALERT !!!");
    Serial.print("Bus at ");
    Serial.print(busData.occupancyPercent);
    Serial.println("% capacity!");
    
    // Beep pattern
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER, HIGH);
      delay(100);
      digitalWrite(BUZZER, LOW);
      delay(100);
    }
    
    alertSent = true;
  } else if (currentStatus != OVERCROWDED) {
    alertSent = false;
  }
}

void displayStartupScreen() {
  lcd.setCursor(0, 0);
  lcd.print("Smart Bus v3.0");
  lcd.setCursor(0, 1);
  lcd.print("Akash Hasendra");
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
  Serial.print("[");
  Serial.print(millis() / 1000);
  Serial.print("s] ");
  Serial.print(eventType);
  Serial.print(" at ");
  Serial.print(location);
  Serial.print(" | Total: ");
  Serial.print(count);
  Serial.print(" | Occupancy: ");
  Serial.print((float)count / MAX_CAPACITY * 100);
  Serial.println("%");
}