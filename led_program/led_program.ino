// --- Status codes ---
// 'B' = busy, 'F' = fail, 'S' = success, 'I' = idle
char busy = 'B';
char fail = 'F';
char success = 'S';
char idle = 'I';

// --- State that must survive between loop() calls ---
unsigned long timeNow = 0;
const unsigned long BLINK_INTERVAL_MS = 300;

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

void setup() {
  for (int i = 0; i < 2; i++) {
    pinMode(triads[i].pinYellow, OUTPUT);
    pinMode(triads[i].pinRed, OUTPUT);
    pinMode(triads[i].pinGreen, OUTPUT);
  }
  Serial.begin(9600);
  Serial.println("READY");
}

void loop() {
  // 1. if a byte is waiting on serial, read it and store in currentStatus
if (Serial.available()) {
  char incoming = Serial.read();
  char normalized = toupper(incoming);
  int index;
  if (normalized == busy || normalized == fail || normalized == idle || normalized == success) {
    // TODO: which triad? isupper(incoming) → asus (index 0), else sandstrom (index 1)
    if(isupper(incoming)) { //asus
      index = 0;
    }
    else{
      index = 1;
    }
    // TODO: store incoming (not normalized) into that triad's currentStatus
    triads[index].currentStatus = incoming;
    }
  }


  // 2. act on currentStatus:
  //    - 'B': non-blocking blink — check millis() - lastToggleTime,
  //           toggle yellowIsOn and update lastToggleTime if interval elapsed
  //    - 'F': red on solid, others off
  //    - 'S': green on solid, others off
  //    - 'I': all off
for (int i = 0; i < 2; i++) {

  if (toupper(triads[i].currentStatus) == idle) {
    digitalWrite(triads[i].pinYellow, LOW);
    digitalWrite(triads[i].pinGreen, LOW);
    digitalWrite(triads[i].pinRed, LOW);
  }

  if (toupper(triads[i].currentStatus) == fail) {
    digitalWrite(triads[i].pinYellow, LOW);
    digitalWrite(triads[i].pinGreen, LOW);
    digitalWrite(triads[i].pinRed, HIGH);
  }

  if (toupper(triads[i].currentStatus) == success) {
    digitalWrite(triads[i].pinYellow, LOW);
    digitalWrite(triads[i].pinGreen, HIGH);
    digitalWrite(triads[i].pinRed, LOW);
  }

  if (toupper(triads[i].currentStatus) == busy) {
    digitalWrite(triads[i].pinGreen, LOW);
    digitalWrite(triads[i].pinRed, LOW);
    timeNow = millis();

    if (timeNow - triads[i].lastToggleTime >= BLINK_INTERVAL_MS) {
      digitalWrite(triads[i].pinYellow, !digitalRead(triads[i].pinYellow));
      triads[i].lastToggleTime = timeNow;
      }
    }
  }
}