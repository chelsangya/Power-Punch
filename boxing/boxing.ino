const int fsrPin1 = A0; // FSR 1 connected to analog pin A0
const int fsrPin2 = A1; // FSR 2 connected to analog pin A1
const int forceThreshold = 350; // Minimum value to consider as a valid force

void setup() {
  Serial.begin(9600); // Initialize serial communication
}

void loop() {
  int fsrReading1 = analogRead(fsrPin1); // Read FSR 1 value
  int fsrReading2 = analogRead(fsrPin2); // Read FSR 2 value

  // Check if either reading exceeds the threshold
  if (fsrReading1 > forceThreshold || fsrReading2 > forceThreshold) {
    int averageForce = (fsrReading1 + fsrReading2) / 2; // Calculate average force

    // Print sensor values and average force to the Serial Monitor
    Serial.println("FSR 1: " + String(fsrReading1) + ", FSR 2: " + String(fsrReading2) + ", Average Force: " + String(averageForce));
    // Serial.println(fsrReading1);
    // Serial.print(", FSR 2: ");
    // Serial.println(fsrReading2);
    // Serial.print(", Average Force: ");
    // Serial.println(averageForce);
  }

  delay(100); // Short delay for stability
}
