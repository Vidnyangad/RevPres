import time
import threading
import subprocess
import sys
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration
PRESENTATION_PATH = "presentation.odp"

# Array of 16 numbers (weights) for slides 2 to 17
weights = [1] * 16

state_lock = threading.Lock()
# state can be: 'IDLE', 'PLAYING', 'PAUSED', 'STOPPING'
current_state = 'IDLE'
current_slide_index = 2 # from 2 to 17
remaining_duration = 0.0 # remaining time for the current slide if paused
total_time = 60.0 # seconds
interrupt_event = threading.Event()

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
            
            for i in range(start_idx, 18):
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
    return render_template('index.html')

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
        
    if 1 <= slide_index <= 16:
        with state_lock:
            current_state = 'PLAYING'
            current_slide_index = slide_index + 1 # goto 1 is slide 2
            remaining_duration = 0.0
            interrupt_event.set()
        return jsonify({"status": "ok", "state": current_state, "goto": slide_index})
    else:
        return jsonify({"status": "error", "message": "Goto must be between 1 and 16"}), 400

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

    app.run(host='0.0.0.0', port=5000)
