# Cube Alarm

This project turns a GAN Bluetooth cube into an alarm clock. When the alarm rings you must solve your cube to dismiss it!

## Backend (Python)

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server
   ```bash
   python backend/alarm_server.py
   ```

## Frontend (React)

1. Install dependencies
   ```bash
   cd frontend
   npm install
   ```
2. Start the dev server
   ```bash
   npm start
   ```

## Getting your cube MAC address

The backend needs the real BLE MAC address of your cube. Run the BLE worker to scan and note the `Manufacturer MAC` it prints:
```bash
python backend/ble_worker.py
```
Set this address in a `.env` file or export `CUBE_MAC` before launching the server.

## Raspberry Pi Setup

### Flashing Raspberry Pi OS

Use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to write
Raspberry Pi OS Lite to a microSD card. Boot the Pi, connect it to your network
then clone this repo and run `setup_pi.sh`.

### Bluetooth

Enable the Bluetooth service and pair your cube if needed:

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### Audio through the headphone jack

Route audio to the 3.5mm jack:

```bash
sudo raspi-config
```

Choose **Advanced Options → Audio → Headphones**.

### Setting volume

You can raise the default volume with PulseAudio:

```bash
pactl set-sink-volume 0 80%
```

### Running the server as a service

`setup_pi.sh` installs a systemd unit named `cube-alarm.service`.
Enable it at boot and start (or restart) it when needed:

```bash
sudo systemctl enable cube-alarm.service
sudo systemctl restart cube-alarm.service
```

Check logs with:

```bash
sudo journalctl -u cube-alarm -f
```

### Serving the React app with nginx

After building the frontend you can serve it with nginx:

```bash
cd frontend
npm install
npm run build
sudo cp -r build/* /var/www/html/
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Hardware

You can purchase the GAN cube used for this project here: [GAN Smart Cube](https://amzn.to/4lgux9D).

## Credits

Huge thanks to [afedotov/gan-web-bluetooth](https://github.com/afedotov/gan-web-bluetooth) for the original logic used to communicate with the cube.

## License

This project is released under the custom license found in `LICENSE.txt`.
