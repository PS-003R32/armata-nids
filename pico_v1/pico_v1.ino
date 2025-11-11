#include <a111125_inferencing.h> //This is the model downloadeed from Edge Imp
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define EI_FEATURE_COUNT 10 //Chacge this according to your model input feature.

LiquidCrystal_I2C lcd(0x27, 16, 2);

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

String inputString = "";
bool stringComplete = false;
String attackerIP = "N/A";
float features[EI_FEATURE_COUNT];

void setup() {
  Serial.begin(115200);
  inputString.reserve(200);
  Wire.begin();
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("NIDS v1.0 Boot..");
  lcd.setCursor(0, 1);
  lcd.print("Waiting for data");

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    lcd.clear();
    lcd.print("OLED Init FAIL");
    while(1);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("NIDS Active");
  display.println("Listening on USB...");
  display.display();
  
  delay(1000);
  lcd.clear();
  display.clearDisplay();
  display.setCursor(0,0);
  display.print("System Ready.");
  display.display();
  lcd.print("System Ready.");
}

void loop() {
  if (stringComplete) {
    bool parseSuccess = parseInputString(inputString);

    if (parseSuccess) {
      signal_t signal;
      int err = numpy::signal_from_buffer(features, EI_FEATURE_COUNT, &signal);
      if (err != 0) {
        ei_printf("Failed to create signal from buffer. Error: %d\n", err);
        lcd.clear();
        lcd.print("Signal Err!");
        return;
      }

      ei_impulse_result_t result;
      err = run_classifier(&signal, &result, false);
      if (err != EI_IMPULSE_OK) {
        ei_printf("Failed to run classifier. Error: %d\n", err);
        lcd.clear();
        lcd.print("Classify Err!");
        return;
      }

      float max_score = 0.0;
      String max_label = "N/A";
      for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        if (result.classification[ix].value > max_score) {
          max_score = result.classification[ix].value;
          max_label = result.classification[ix].label;
        }
      }
      
      updateDisplays(max_label, max_score);
      Serial.println("ACK: " + max_label);

    } else {
      lcd.clear();
      lcd.print("Serial Parse_Err");
      Serial.println("ERR: Parse failed");
    }

    inputString = "";
    stringComplete = false;
  }
}

void updateDisplays(String label, float score) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("LastScan:" + label);

  if (label != "BENIGN") {
    lcd.setCursor(0, 1);
    lcd.print("!ATTACK DETECTED!");

    display.clearDisplay();
    display.setCursor(0, 0);
    display.setTextSize(2);
    display.println("! ALERT !");
    display.setTextSize(1);
    display.println("TYPE: " + label);
    display.println("CONF: " + String(score * 100, 1) + "%");
    display.println("SRC IP: " + attackerIP);
    display.display();
    
  } else {
    lcd.setCursor(0, 1);
    lcd.print("Status:AllClear");
    
    display.clearDisplay();
    display.setCursor(0, 0);
    display.setTextSize(1);
    display.println("NIDS Active");
    display.println("Status: All Clear");
    display.println("LastSeen:" + attackerIP);
    display.println("LastType: BENIGN");
    display.display();
  }
}

bool parseInputString(String input) {
  input.trim();
  if (input.length() == 0) return false;

  int commaIndex = input.indexOf(',');
  if (commaIndex == -1) return false;

  attackerIP = input.substring(0, commaIndex);
  String featureString = input.substring(commaIndex + 1);

  int featureIndex = 0;
  int lastIndex = 0;
  
  for (int i = 0; i < featureString.length(); i++) {
    if (featureString.charAt(i) == ',') {
      if (featureIndex < EI_FEATURE_COUNT) {
        features[featureIndex] = featureString.substring(lastIndex, i).toFloat();
        featureIndex++;
        lastIndex = i + 1;
      } else {
        return false;
      }
    }
  }

  if (featureIndex < EI_FEATURE_COUNT) {
    features[featureIndex] = featureString.substring(lastIndex).toFloat();
    featureIndex++;
  }

  return (featureIndex == EI_FEATURE_COUNT);
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}
