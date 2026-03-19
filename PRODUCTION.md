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

## 3. Running as a Service on Boot (systemd)

To make the application run automatically whenever the Raspberry Pi turns on, you can create a `systemd` service.

1. Create a new service file:
```bash
sudo nano /etc/systemd/system/presentation.service
```

2. Paste the following configuration (adjust the paths to match where your project is stored):

```ini
[Unit]
Description=Gunicorn instance to serve the Presentation Controller
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/your-repository
Environment="PATH=/home/pi/your-repository/venv/bin"
Environment="DISPLAY=:0"
ExecStart=/home/pi/your-repository/venv/bin/gunicorn -w 1 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```
*Note: The `Environment="DISPLAY=:0"` line is crucial so that the application knows which screen to launch LibreOffice on.*

3. Start and enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start presentation
sudo systemctl enable presentation
```

You can check the status and logs of your application at any time using:
```bash
sudo systemctl status presentation
```
