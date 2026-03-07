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
# state can be: 'IDLE', 'PLAYING', 'GOTO', 'STOPPING'
current_state = 'IDLE'
current_goto = None
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
    global current_state, current_goto, total_time
    
    while True:
        with state_lock:
            state = current_state
            goto_slide = current_goto
            tt = total_time
            
        if state == 'IDLE':
            # Wait until we are woken up by an action
            interrupt_event.wait()
            interrupt_event.clear()
            
        elif state == 'STOPPING':
            # Go to title slide and become IDLE
            go_to_slide(1)
            with state_lock:
                if current_state == 'STOPPING':
                    current_state = 'IDLE'
            
        elif state == 'PLAYING':
            # Play slides 2 to 17
            finished_normally = True
            total_weight = sum(weights)
            
            for i in range(2, 18):
                with state_lock:
                    if current_state != 'PLAYING':
                        finished_normally = False
                        break # State changed to something else, exit loop
                
                go_to_slide(i)
                
                weight = weights[i-2]
                duration = (weight / total_weight) * tt
                
                # Sleep for duration, interruptible
                interrupted = interrupt_event.wait(timeout=duration)
                if interrupted:
                    interrupt_event.clear()
                    finished_normally = False
                    break # State changed or Start pressed again
            
            # After playing all slides or being interrupted
            if finished_normally:
                with state_lock:
                    if current_state == 'PLAYING':
                        # Finished normally, transition to STOPPING so it goes to slide 1
                        current_state = 'STOPPING'

        elif state == 'GOTO':
            # Goto specific slide (goto_slide is 1-16, corresponding to slide 2-17)
            target_slide = goto_slide + 1
            go_to_slide(target_slide)
            
            total_weight = sum(weights)
            weight = weights[goto_slide - 1]
            duration = (weight / total_weight) * tt
            
            interrupted = interrupt_event.wait(timeout=duration)
            if interrupted:
                interrupt_event.clear()
                # Interrupted by something else
            else:
                # Finished normally
                with state_lock:
                    if current_state == 'GOTO':
                        current_state = 'STOPPING'

# Start the worker thread
worker_thread = threading.Thread(target=presentation_worker, daemon=True)
worker_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start():
    global current_state, total_time
    data = request.json or {}
    
    if 'total_time' in data:
        try:
            total_time = float(data['total_time'])
        except ValueError:
            pass
            
    with state_lock:
        current_state = 'PLAYING'
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
    global current_state, current_goto, total_time
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
            current_state = 'GOTO'
            current_goto = slide_index
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
