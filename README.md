# Raspberry Pi Presentation Controller

This is a Flask-based web application designed to run on a Raspberry Pi to control a LibreOffice Impress presentation using `xdotool`.

## Features
- Serve a web page with **Start**, **Stop**, and **Goto** buttons.
- Calculate slide duration dynamically based on the "Total Time (s)" input and an internal weighting array.
- Transition through slides (2 to 17) or specifically target one, returning to slide 1 afterwards or if interrupted.

## Setup

### 1. Prerequisites
You need to have LibreOffice and `xdotool` installed on your Raspberry Pi:

```bash
sudo apt update
sudo apt install libreoffice xdotool
```

### 2. Python Dependencies
Ensure you have Python 3 and `pip` installed. On a Raspberry Pi, it's recommended to create a virtual environment for Python packages to avoid conflicts with system-managed packages:

```bash
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Running LibreOffice Impress
Open your 17-slide LibreOffice Impress presentation and start the slideshow.

```bash
libreoffice --show path/to/presentation.odp
```
Make sure the LibreOffice presentation has the active focus so `xdotool` can send keystrokes to it.

### 4. Running the Web Application
Start the Flask application:

```bash
python3 app.py
```
The application will run on `0.0.0.0:5000`. You can access it via a web browser from any device on the same network using the Raspberry Pi's IP address: `http://<raspberry_pi_ip>:5000`.
