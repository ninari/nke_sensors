FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    gcc \
    python3-rpi.gpio \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app
COPY requirements.txt .
COPY sensor.py /app/
COPY metadata.json /app/
# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



RUN pip install flask
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install RPi.GPIO adafruit-blinka
RUN pip install RPi.GPIO adafruit-blinka
RUN apt-get update && apt-get install -y python3-rpi.gpio
RUN pip install smbus2

# Create venv
RUN python -m venv /app/.venv
RUN /app/.venv/bin/python -m pip install --upgrade pip setuptools wheel




EXPOSE 5437



COPY . .
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5437", "sensor:app"]
#CMD ["/home/workspace/.local/analog-sensor-extension/.venv/bin/python", "/home/workspace/.local/analog-sensor-extension/sensor.py"]
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "sensor.py"]