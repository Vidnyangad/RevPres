import time
import threading
import subprocess
import sys
import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    GPIO_AVAILABLE = False
    print(f"Warning: RPi.GPIO module not found or could not be loaded ({e}). Physical button support disabled.")

load_dotenv()

app = Flask(__name__)

# Configuration from Environment Variables
PRESENTATION_PATH = os.environ.get("PRESENTATION_PATH", "presentation.odp")
try:
    TOTAL_SLIDES = int(os.environ.get("TOTAL_SLIDES", "16"))
except ValueError:
    TOTAL_SLIDES = 16

# Parse weights if provided, otherwise default to 1 for all slides
weights_str = os.environ.get("WEIGHTS")
if weights_str:
    try:
        weights = json.loads(weights_str)
        if len(weights) != TOTAL_SLIDES:
            print(f"Warning: Number of weights ({len(weights)}) does not match TOTAL_SLIDES ({TOTAL_SLIDES}). Defaulting to 1 for all.")
            weights = [1] * TOTAL_SLIDES
    except json.JSONDecodeError:
        print("Warning: WEIGHTS environment variable is not valid JSON. Defaulting to 1 for all.")
        weights = [1] * TOTAL_SLIDES
else:
    weights = [1] * TOTAL_SLIDES

state_lock = threading.Lock()
# state can be: 'IDLE', 'PLAYING', 'PAUSED', 'STOPPING'
current_state = 'IDLE'
current_slide_index = 2 # from 2 to TOTAL_SLIDES + 1
remaining_duration = 0.0 # remaining time for the current slide if paused
total_time = 60.0 # seconds
interrupt_event = threading.Event()

# GPIO Setup
BUTTON_PIN = 17

def handle_button_press(channel):
    global current_state, current_slide_index, remaining_duration

    with state_lock:
        if current_state != 'PAUSED':
            current_slide_index = 2
            remaining_duration = 0.0
        current_state = 'PLAYING'
        interrupt_event.set()
    print("Physical button pressed: Starting presentation")

if GPIO_AVAILABLE:
    try:
        GPIO.setmode(GPIO.BCM)
        # Use internal pull-up resistor
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Add event detect on FALLING edge (button press connects to ground)
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=handle_button_press, bouncetime=300)
        print(f"GPIO setup complete. Listening on pin {BUTTON_PIN}.")
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        GPIO_AVAILABLE = False

def go_to_slide(slide_number):
    try:
        # We can send 'type' and 'Return'
        subprocess.run(['xdotool', 'type', str(slide_number)], check=False)
        subprocess.run(['xdotool', 'key', 'Return'], check=False)
    except Exception as e:
        print(f"Error going to slide: {e}")

def presentation_worker():
    global current_state, current_slide_index, total_time, remaining_duration
    
    while True:
        with state_lock:
            state = current_state
            tt = total_time
            start_idx = current_slide_index
            rem_dur = remaining_duration
            
        if state == 'IDLE':
            # Wait until we are woken up by an action
            interrupt_event.wait()
            interrupt_event.clear()
            
        elif state == 'PAUSED':
            # Wait until we are woken up to resume or stop
            interrupt_event.wait()
            interrupt_event.clear()

        elif state == 'STOPPING':
            # Go to title slide and become IDLE
            go_to_slide(1)
            with state_lock:
                if current_state == 'STOPPING':
                    current_state = 'IDLE'
                    current_slide_index = 2
                    remaining_duration = 0.0
            
        elif state == 'PLAYING':
            finished_normally = True
            total_weight = sum(weights)
            
            for i in range(start_idx, TOTAL_SLIDES + 2):
                with state_lock:
                    if current_state != 'PLAYING':
                        finished_normally = False
                        break # State changed, exit loop

                # Update current slide in state lock so Pause knows where we are
                with state_lock:
                    current_slide_index = i
                
                # Only go to the slide if we aren't resuming from a pause on this exact slide,
                # or if we are just starting this slide. To simplify, we'll go to the slide.
                go_to_slide(i)
                
                weight = weights[i-2]

                # If we have a remaining duration from a pause, use it. Otherwise calculate full duration.
                if rem_dur > 0:
                    duration = rem_dur
                    with state_lock:
                        remaining_duration = 0.0 # Clear global after use
                    rem_dur = 0.0 # Clear local after use
                else:
                    duration = (weight / total_weight) * tt

                start_time = time.time()
                
                # Sleep for duration, interruptible
                interrupted = interrupt_event.wait(timeout=duration)
                if interrupted:
                    interrupt_event.clear()
                    finished_normally = False

                    # Calculate remaining time if we were paused
                    elapsed = time.time() - start_time
                    with state_lock:
                        if current_state == 'PAUSED':
                            remaining_duration = max(0.0, duration - elapsed)
                        # If current_state is still PLAYING, it means Start or Goto was pressed.
                        # The route handler already updated current_slide_index and remaining_duration appropriately.
                    break # State changed or Start/Goto pressed again
            
            # After playing all slides or being interrupted
            if finished_normally:
                with state_lock:
                    if current_state == 'PLAYING':
                        # Finished normally, transition to STOPPING so it goes to slide 1
                        current_state = 'STOPPING'

# Start the worker thread
worker_thread = threading.Thread(target=presentation_worker, daemon=True)
worker_thread.start()

@app.route('/')
def index():
    return render_template('index.html', total_slides=TOTAL_SLIDES)

@app.route('/api/start', methods=['POST'])
def start():
    global current_state, total_time, current_slide_index, remaining_duration
    data = request.json or {}
    
    if 'total_time' in data:
        try:
            total_time = float(data['total_time'])
        except ValueError:
            pass
            
    with state_lock:
        if current_state != 'PAUSED':
            current_slide_index = 2
            remaining_duration = 0.0
        current_state = 'PLAYING'
        interrupt_event.set()
        
    return jsonify({"status": "ok", "state": current_state})

@app.route('/api/pause', methods=['POST'])
def pause():
    global current_state

    with state_lock:
        if current_state == 'PLAYING':
            current_state = 'PAUSED'
            interrupt_event.set()

    return jsonify({"status": "ok", "state": current_state})

@app.route('/api/stop', methods=['POST'])
def stop():
    global current_state
    
    with state_lock:
        current_state = 'STOPPING'
        interrupt_event.set()
        
    return jsonify({"status": "ok", "state": current_state})

@app.route('/api/goto', methods=['POST'])
def goto():
    global current_state, current_slide_index, remaining_duration, total_time
    data = request.json or {}
    
    if 'total_time' in data:
        try:
            total_time = float(data['total_time'])
        except ValueError:
            pass
            
    try:
        slide_index = int(data.get('goto', 1))
    except ValueError:
        return jsonify({"status": "error", "message": "Goto must be an integer"}), 400
        
    if 1 <= slide_index <= TOTAL_SLIDES:
        with state_lock:
            current_state = 'PLAYING'
            current_slide_index = slide_index + 1 # goto 1 is slide 2
            remaining_duration = 0.0
            interrupt_event.set()
        return jsonify({"status": "ok", "state": current_state, "goto": slide_index})
    else:
        return jsonify({"status": "error", "message": f"Goto must be between 1 and {TOTAL_SLIDES}"}), 400

def start_presentation(presentation_path):
    print(f"Starting LibreOffice presentation: {presentation_path}")
    try:
        # Launch libreoffice in show mode
        subprocess.Popen(['libreoffice', '--show', presentation_path])

        # Give LibreOffice some time to open
        time.sleep(5)

        # Try to focus the window. LibreOffice Impress slideshow windows typically have class 'Soffice'
        # We search for a window with name starting with 'LibreOffice' or class 'Soffice'
        try:
            # We use xdotool search to find the window and windowactivate to focus it.
            # Usually, the presentation window is the active one, but just in case:
            subprocess.run(['xdotool', 'search', '--class', 'Soffice', 'windowactivate'], check=False)
        except Exception as e:
            print(f"Could not focus window: {e}")

    except Exception as e:
        print(f"Error starting presentation: {e}")

if __name__ == '__main__':
    if os.path.exists(PRESENTATION_PATH):
        # Start the presentation in a separate thread so we don't block Flask startup
        threading.Thread(target=start_presentation, args=(PRESENTATION_PATH,), daemon=True).start()
    else:
        print(f"Warning: Presentation file '{PRESENTATION_PATH}' not found. Please check PRESENTATION_PATH in app.py.")

    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                print("Cleaned up GPIO.")
            except Exception as e:
                print(f"Error during GPIO cleanup: {e}")
