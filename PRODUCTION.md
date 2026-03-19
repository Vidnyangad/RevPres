# Production Deployment with Gunicorn

The Flask development server (`app.run()`) is not designed for production use on a Raspberry Pi. It is recommended to use a robust WSGI server like **Gunicorn**. 

Because this application controls a single physical LibreOffice instance and manages physical Raspberry Pi GPIO pins, it is **critical** that you only run a single worker process (`-w 1`). Multiple workers will attempt to access the same GPIO pins simultaneously, leading to crashes or unpredictable hardware behavior.

## 1. Install Gunicorn

First, ensure your virtual environment is activated, then install Gunicorn via pip:

```bash
source venv/bin/activate
pip install gunicorn
```

You can optionally add `gunicorn` to your `requirements.txt`.

## 2. Running with Gunicorn (Manual)

To run the application manually using Gunicorn, execute the following command from your project directory:

```bash
gunicorn -w 1 -b 0.0.0.0:5000 app:app
```

- `-w 1`: Instructs Gunicorn to use exactly 1 worker process.
- `-b 0.0.0.0:5000`: Binds the server to all network interfaces on port 5000.
- `app:app`: Points to the `app` instance inside the `app.py` file.

## 3. Running Automatically on Desktop Startup

Because this application relies on a graphical desktop environment (X11) to launch the LibreOffice presentation, it is highly recommended to run it via the Raspberry Pi OS autostart system rather than a background `systemd` service. This guarantees the application only runs *after* the desktop has fully loaded and automatically gives it access to the active display screen.

1. Ensure the `autostart` directory exists:
```bash
mkdir -p /home/pi/.config/autostart
```

2. Create a new `.desktop` autostart file:
```bash
nano /home/pi/.config/autostart/presentation.desktop
```

3. Paste the following configuration (adjust the paths to match where your repository is located):

```ini
[Desktop Entry]
Type=Application
Name=Presentation Controller
Comment=Start the Flask Presentation Controller and LibreOffice
Exec=bash -c 'cd /home/pi/your-repository && source venv/bin/activate && gunicorn -w 1 -b 0.0.0.0:5000 app:app > gunicorn.log 2>&1'
StartupNotify=false
Terminal=false
```

4. Reboot your Raspberry Pi. The desktop environment will load, and immediately afterwards, the autostart script will activate your Python virtual environment, start Gunicorn, and automatically launch the LibreOffice presentation.

