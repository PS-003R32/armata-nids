# armata-nids
This network intrusion detection system uses least hardware that is required to run a simple and effective NIDS. I have used a raspberry pi pico wh, zero w, ssd1306 oled and 1602 lcd displays for this project.
This project uses a Neural Network Classifier model trained on the `CIC IDS 2017` dataset and is trained on the `Edge Impulse` platform. I will provide the links and references to the trained model of my Edge Impulse profile below in the setup guide. [NOTE: This project is in contineous improvement and development, you might get some problems if you dont have the minimum hardware that i have used. You can pull a new Issue if you find any errors or have any suggestions. [Video](https://www.youtube.com/watch?v=zJ92Vnly6WM) Demonstration.<br>
<img src="https://github.com/user-attachments/assets/e182de03-e594-43a2-a816-a4ea613a8525" alt="hwd" width="270"/>

---
## Hardware
This is the minimum hardware required to develop and run this nids:
- Raspberry pi zero w (has a 32-bit processor, running raspberry pi os lite).
- Raspberry pi pico wh.
- SSD1306 OLED
- 1602 LCD
- Jumper wires and breadboard. (if you need)
### Hardware connections
Data and clock serial pins will be common for both the displays.<br>
Connect:<br>
The serial data and clock, ground and vcc will be common for both the displays and connect to the pico , set the common lines on a breadboard:<br>
|            Pico WH           | SSD1306 & 1602 LCD |
|------------------------------|--------------------|
| VBUS (Pin 40) or 3V3 (Pin 36) | VCC                |
| GND (Pin 38)                 | GND                |
| GPIO4 (Pin 6)                | SDA (Data Line)    |
| GPIO5 (Pin 7)                | SCL (Clock Line)   |

### Pico wh to zero w
You can either use the usb connection or use UART RX/TX for communication b/w pico and zero, i have used usb for ease. but you can connect using rx/tx by connecting pico RX (pin 22) to zero TX (pin 8) and pico TX (pin 21) to zero RX pin 10, a gnd wire to both the boards.

---

## Softwares required
Before you start make sure to install the folowing packages and applications.
- Arduino IDE<br>
You can use the dataset i have provided in this repository or download it from [here](http://cicresearch.ca/CICDataset/CIC-IDS-2017/Dataset/CIC-IDS-2017/CSVs/) to train your own model and your required features input/output. But i will recommend to use the model i trained in this repository or download it from my Edge Impulse profile [here](https://studio.edgeimpulse.com/public/823138/live).
- Download the zip file `ei-111125-arduino-1.0.1`.
#### create your own training set
Just place the `dataCL.py` file in the same directory as the `MachineLearningCSV` then adjust the samples accordingly as the comment i have added in the dataCl.py file. You will get the compiled training dataset to train your own model.

 ---

 ## Seting up 
First we will program the pico wh board using the Arduino IDE. Open the ide and go to *Sketch > Include Library > Add .ZIP Library...* then select the `ei-111125-arduino-1.0.1` you downloaded to install the classifier. Now go to *Tools > Board > Boards Manager...> [search and Install Raspberry Pi Pico/RP2040/RP2350] by Earle F. Philhover, III* then again go to *Tools > Board > Raspberry Pi Pico/RP2040/RP2350 > Raspberry Pi Pico W* to make the IDE identify the development board. <br>
Now Go to *Tools > Port > UF2_Board*.<br>
NOw install the following libraries:-
```text
Go to Tools > Manage Libraries... > and then search and install the following libraries
LiquidCrystal_I2C
Adafruit_GFX
Adafruit_SSD1306
```
Now download the `ei-111125-arduino-1.0.1` as well as the `pico_v1.ino` file. Open the file in the Arduino IDE and clivk on the Verify and Upload button to upload it to pico wh. If you see any errors related to the inbuilt libraries do not worry it will still work its just the errors for compatiblity or old libraries syntax which have no effect on the pico.<br>
#### pico wh to zero w
I have used usb to connect the pico to the zero for simplicity but you can use UART RX/TX connection if you want, you can find the pin connection below. You have to change the `PICO_SERIAL_PORT = '/dev/ttyACM0'` in the `zero_opt.py` line 9 to `PICO_SERIAL_PORT = '/dev/serial0'` (its usually this but you can find the exact one by `ls /dev/serial*` or for usb `ls /dev/tty*`).<br>

 ---
 Install the following libraries on the zero.
 ```shell
sudo pip3 install scapy numpy pyserial
---install individually if the zero stops responding as it just has a 1ghz cpu.---
```
Now you just need to run the python script to start the nids. `sudo python3 zero_opt.py`.

---
If any errors you can state it in the discussions.
