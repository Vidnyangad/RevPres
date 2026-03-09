# Raspberry Pi Presentation Controller

This is a Flask-based web application designed to run on a Raspberry Pi to control a LibreOffice Impress presentation using `xdotool`.

## Features
- Serve a web page with **Start**, **Stop**, and **Goto** buttons.
- Calculate slide duration dynamically based on the "Total Time (s)" input and an internal weighting array.
- Transition through slides (2 to 17) or specifically target one, returning to slide 1 afterwards or if interrupted.

## Setup

### 1. Prerequisites
You need to have LibreOffice, `git`, and `xdotool` installed on your Raspberry Pi:

```bash
sudo apt update
sudo apt install libreoffice xdotool git
```

### 2. Download the Software
Clone the repository to your Raspberry Pi:

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

### 3. Python Dependencies
Ensure you have Python 3 and `pip` installed. On a Raspberry Pi, it's recommended to create a virtual environment for Python packages to avoid conflicts with system-managed packages:

```bash
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory (you can copy `.env.example` as a starting point) to configure the application.

```env
# Path to your presentation file
PRESENTATION_PATH="path/to/your/presentation.odp"

# Total number of slides (excluding the title slide, e.g., if you have 17 slides in total, this should be 16)
TOTAL_SLIDES=16

# Array of weights for each slide's duration, formatted as a JSON array string.
# Must contain exactly TOTAL_SLIDES numbers. Defaults to [1, 1, ...] if omitted.
WEIGHTS="[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]"
```

### 5. Running the Web Application
Start the Flask application:

```bash
python3 app.py
```
The application will automatically start LibreOffice Impress in presentation mode and bring it to focus. It will then run on `0.0.0.0:5000`. You can access it via a web browser from any device on the same network using the Raspberry Pi's IP address: `http://<raspberry_pi_ip>:5000`.
