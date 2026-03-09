# Wiring Instructions for Physical Start Button

You can add a physical, hardwired Normally Open (NO) push button to trigger the "Start" function of the presentation.

## Hardware Required
*   1x Normally Open (NO) Push Button
*   2x Jumper Wires

## Pinout and Wiring

We will be using **GPIO 17** (Pin 11 on the Raspberry Pi header) and any **Ground (GND)** pin (such as Pin 9 or Pin 14).

Because the application is configured to use the Raspberry Pi's **internal pull-up resistor** on GPIO 17, no external resistors are required.

### Connections:

1.  Connect **one side** of the NO push button to **GPIO 17 (Pin 11)**.
2.  Connect the **other side** of the NO push button to a **Ground (GND)** pin (e.g., Pin 9 or Pin 14).

## How it works
*   The internal pull-up resistor keeps GPIO 17 HIGH (3.3V) when the button is not pressed.
*   When you press the button, it closes the circuit to Ground, pulling GPIO 17 LOW (0V).
*   The software detects this falling edge (transition from HIGH to LOW) and triggers the presentation to Start.
