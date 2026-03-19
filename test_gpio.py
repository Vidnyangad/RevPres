import time

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError) as e:
    print(f"Error importing RPi.GPIO: {e}")
    print("This script must be run on a Raspberry Pi!")
    exit(1)

BUTTON_PIN = 17

def setup():
    try:
        GPIO.setmode(GPIO.BCM)
        # Match app.py: Use internal pull-up resistor
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"GPIO setup complete. Polling on pin {BUTTON_PIN}.")
        print("Press the button (pulling pin to GND) to test...")
        print("Press Ctrl+C to exit.\n")
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        exit(1)

def loop():
    try:
        while True:
            current_state = GPIO.input(BUTTON_PIN)
            if current_state == GPIO.LOW:
                print(f"[{time.strftime('%H:%M:%S')}] Button IS PRESSED (Pin 17 is LOW)")
            else:
                pass # Un-comment below to spam the terminal when not pressed
                # print(f"[{time.strftime('%H:%M:%S')}] Button is NOT pressed (Pin 17 is HIGH)")

            time.sleep(0.1) # 100ms
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    setup()
    try:
        loop()
    finally:
        GPIO.cleanup()
        print("\nCleaned up GPIO. Exiting test.")
