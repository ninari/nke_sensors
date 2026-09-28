#!/bin/sh
# Activate venv
. /app/.venv/bin/activate

# Run service
exec python /app/sensor.py

#!/bin/sh
. /home/workspace/.local/analog-sensor-extension/.venv/bin/activate
exec python /home/workspace/.local/analog-sensor-extension/sensor.py
