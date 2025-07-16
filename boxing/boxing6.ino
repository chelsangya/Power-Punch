const int fsrPin1 = A0;         // FSR 1 connected to analog pin A0
const int fsrPin2 = A3;   
const int fsrPin3 = A5; 
const int fsrPin4 = A1;
const int fsrPin5 = A2;
const int fsrPin6 = A4;  

//FSR 2 connected to analog pin A1
const int forceThreshold = 350; // Minimum value to consider as a valid force

void setup()
{
  Serial.begin(9600); // Initialize serial communication
}


void loop()
{
 int fsrReading1 = analogRead(fsrPin1); // Read FSR 1 value
 int fsrReading2 = analogRead(fsrPin2); // Read FSR 2 value
int fsrReading3 = analogRead(fsrPin3);
int fsrReading4 = analogRead(fsrPin4); // Read FSR 1 value
 int fsrReading5 = analogRead(fsrPin5); // Read FSR 2 value
int fsrReading6 = analogRead(fsrPin6);
 // Check if either reading exceeds the threshold
 if (fsrReading1 > forceThreshold || fsrReading2 > forceThreshold || fsrReading3 > forceThreshold || fsrReading4 > forceThreshold || fsrReading5 > forceThreshold || fsrReading6 > forceThreshold)
  {
    int averageForce = (fsrReading1 + fsrReading2 + fsrReading3 + fsrReading4 + fsrReading5 + fsrReading6) / 6; 

   // Print sensor values and average force to the Serial Monitor
   Serial.println("FSR 1: " + String(fsrReading1) + ", FSR 2: " + String(fsrReading2) + ",  FSR 3: " + String(fsrReading3) + ", FSR 4: " + String(fsrReading4) +", FSR 5: " + String(fsrReading5) + ", FSR 6: " + String(fsrReading6) +  ", Average Force: " + String(averageForce) );
   Serial.println(fsrReading1);
  Serial.print(", FSR 2: ");
  Serial.println(fsrReading2);
 Serial.print(", Average Force: ");
Serial.println(averageForce);
  }

 delay(100); // Short delay for stability
}