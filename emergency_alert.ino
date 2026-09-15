int buzzer = 8;
int redLED = 9;
int greenLED = 10;

void setup() {

  pinMode(buzzer, OUTPUT);
  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);

  // Normal mode
  digitalWrite(buzzer, LOW);
  digitalWrite(redLED, LOW);
  digitalWrite(greenLED, HIGH);

  Serial.begin(9600);
}

void loop() {

  if (Serial.available() > 0) {

    char command = Serial.read();

    if (command == 'E') {

      // Emergency mode
      digitalWrite(greenLED, LOW);
      digitalWrite(redLED, HIGH);
      digitalWrite(buzzer, HIGH);

      delay(10000);

      // Back to normal
      digitalWrite(buzzer, LOW);
      digitalWrite(redLED, LOW);
      digitalWrite(greenLED, HIGH);
    }
  }
}