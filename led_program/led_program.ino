// --- Pin assignments (fill in the digital pins you've wired) ---
const int PIN_LED_YELLOW = 8;
const int PIN_LED_RED    = 9;
const int PIN_LED_GREEN  = 10;

// --- Status codes ---
// 'B' = busy, 'F' = fail, 'S' = success, 'I' = idle
char busy = 'B';
char fail = 'F';
char success = 'S';
char idle = 'I';

// --- State that must survive between loop() calls ---
char currentStatus = 'I';
unsigned long lastToggleTime = 0;
unsigned long timeNow = 0;
const unsigned long BLINK_INTERVAL_MS = 300;

void setup() {
  // pinMode() each LED pin as OUTPUT
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  // Serial.begin() at some baud rate
  Serial.begin(9600);
  Serial.println("READY");
}

struct Triad {
  int pinYellow;
  int pinRed;
  int pinGreen;
  char currentStatus;
  unsigned long lastToggleTime;
};

Triad triads[2] = {
  // asus  — pins 10/9/8, initial status 'I', lastToggleTime 0
  {10, 9, 8, 'I', 0,},
  // sandstrom — pins 7/6/5, initial status 'i', lastToggleTime 0
  {7, 6, 5, 'i', 0}
};

void loop() {
  // 1. if a byte is waiting on serial, read it and store in currentStatus
  if (Serial.available()) {
    char incoming = Serial.read();
    if (incoming == busy || incoming == fail || incoming == idle || incoming == success){
      currentStatus = incoming;
    }
}

  // 2. act on currentStatus:
  //    - 'B': non-blocking blink — check millis() - lastToggleTime,
  //           toggle yellowIsOn and update lastToggleTime if interval elapsed
  //    - 'F': red on solid, others off
  //    - 'S': green on solid, others off
  //    - 'I': all off
  if (currentStatus == idle) {
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_RED, LOW);
  }

  if (currentStatus == fail) {
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_RED, HIGH);
  }

  if (currentStatus == success) {
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_LED_RED, LOW);
  }

  if (currentStatus == busy) {
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_RED, LOW);
    timeNow = millis();

    if (timeNow - lastToggleTime >= BLINK_INTERVAL_MS) {
      digitalWrite(PIN_LED_YELLOW, !digitalRead(PIN_LED_YELLOW));
      lastToggleTime = timeNow;
    }
  }
}