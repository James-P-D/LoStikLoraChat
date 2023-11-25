# LoStikLoraChat
Simple text chat client for the LoStik Lora device using Python and PySimpleGUI for UI

![Screenshot](https://github.com/James-P-D/LoStikLoraChat/blob/main/screenshot.gif)

## Introduction

Since I'm just getting started with [Lora](https://en.wikipedia.org/wiki/LoRa), I decided to create a simple chat application in Python with a UI in PySimpleGUI. The application uses the [Ronoth LoStik](https://ronoth.com/products/lostik) device:

![LoStiks](https://github.com/James-P-D/LoStikLoraChat/blob/main/LoStiks.jpg)

## Running

The LoStik device communicates over a COM port on Windows, so we need to install `pyserial`. The UI uses PySimpleGUI so we also need that:

```
pip install PySimpleGUI
pip install pyserial
```

To run the program:

```
python main.py
```

You will then see the UI. You can click the <kbd>Settings</kbd> button if you wish to change the frequency, power, bandwidth or spread settings:

![Settings](https://github.com/James-P-D/LoStikLoraChat/blob/main/settings.png)

Enter the COM port your LoStik device is connected to, press the <kbd>Connect</kbd> button. If `Debug Mode` is turned on, you should see the strings being send back and forth to the LoStik. Now enter you message in the textbox and click <kbd>Send</kbd>.