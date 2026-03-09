# Physical Start Button Wiring Guide

This guide explains how to connect a physical Normally Open (NO) push button to your Raspberry Pi to trigger the presentation "Start" function, mirroring the behavior of the "Start" button on the web interface.

## What You Need
- 1 x Normally Open (NO) Push Button / Momentary Switch
- 2 x Jumper wires (Female-to-Female if connecting directly to the Pi's pins)
- 1 x Raspberry Pi (Any model with standard 40-pin GPIO headers)

## Wiring Instructions

The software is configured to use **GPIO 17** (Physical Pin 11) for the Start button. We will use the Raspberry Pi's internal pull-up resistor, meaning you **do not** need to add an external resistor to your circuit.

1. Connect **one side** of your NO push button to **Physical Pin 11** (GPIO 17) on the Raspberry Pi.
2. Connect the **other side** of your NO push button to any **Ground (GND)** pin on the Raspberry Pi. For convenience, **Physical Pin 9** is right next to Pin 11.

### Raspberry Pi Pinout Reference
Here is a simplified view of the top-left section of the GPIO header:

```
[Pin 1] 3.3V  | [Pin 2] 5V
[Pin 3] GPIO2 | [Pin 4] 5V
[Pin 5] GPIO3 | [Pin 6] GND
[Pin 7] GPIO4 | [Pin 8] GPIO14
[Pin 9] GND   | [Pin 10] GPIO15
[Pin 11] GPIO17 <--- Connect Button Side 1
...
```

## How It Works
1. The software configures GPIO 17 as an input and activates the internal pull-up resistor, keeping the pin's state `HIGH` (3.3V) by default.
2. When you press the button, it bridges the connection to the Ground pin, pulling the state on GPIO 17 `LOW` (0V).
3. The software detects this "falling edge" and immediately triggers the presentation to Start (or restart from slide 2 if already playing), exactly as if you clicked the Start button on the web page.

## Changing the Pin
If you need to use a different GPIO pin, open `app.py` in a text editor, locate the `START_BUTTON_PIN` configuration variable near the top, and change it from `17` to your preferred Broadcom (BCM) GPIO pin number.