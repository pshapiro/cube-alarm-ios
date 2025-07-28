# Cube Alarm

This repository contains the server and frontend code for the Rubik's Cube alarm clock.

## API Endpoints

The backend exposes a small set of HTTP routes for managing alarms and cube state.

- `GET /api/alarms` – retrieve all alarms
- `GET /api/alarms/active` – list alarms that are currently ringing
- `POST /api/alarms` – create a new alarm
- `PUT /api/alarms/<id>` – update an alarm
- `DELETE /api/alarms/<id>` – delete an alarm
- `POST /api/alarms/<id>/stop` – stop a specific alarm
- `POST /api/alarms/stop` – stop all alarms
