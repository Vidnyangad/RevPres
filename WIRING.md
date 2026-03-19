# Hardware Wiring Instructions

This document explains how to connect a physical Normally Open (NO) push button to the Raspberry Pi to trigger the presentation "Start" function.

## Prerequisites

- Raspberry Pi
- Normally Open (NO) push button switch
- Two jumper wires

## Wiring Instructions

You will connect the two terminals of your push button to the Raspberry Pi GPIO header. It does not matter which wire goes to which terminal on the button.

1.  **Pin 1:** Connect one side of the push button to **GPIO 27** (which is Physical Pin 13 on the Raspberry Pi header).
2.  **Pin 2:** Connect the other side of the push button to any **Ground (GND)** pin. For example, Physical Pin 9 or Physical Pin 14.

### Why this works
The application uses the Raspberry Pi's internal pull-up resistor on GPIO 27. This means the pin is naturally held at a HIGH voltage state.
When the button is pressed, it connects the pin to Ground, pulling the voltage LOW. The software detects this HIGH-to-LOW transition (falling edge) and triggers the presentation to start.

Because we are using the internal pull-up resistor, no external resistors are required.
