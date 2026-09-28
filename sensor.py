from flask import Flask, jsonify, render_template, send_from_directory, Response
from flask import request
from collections import deque
from flask import send_file
import os
import random
import datetime
import time, threading
import logging
import math
import board
import busio
import math
import serial
from collections import Counter

import csv

from pymodbus.server import StartSerialServer
from pymodbus.client import ModbusSerialClient
from pymodbus.framer import FramerType
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock


values = []


latest_value = None
min_value = None
max_value = None
most_common_value = None   # <-- add this line


# გახსენი სერიალური პორტი
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1) 



def safe_value(val):
    if val is None or math.isnan(val):
        return None   # JSON-ში ეს გახდება null
    return val


def get_sensor_data():
    # აირჩიე მნიშვნელობა პრიორიტეტით: most_common_value → latest_value → 0.0
    if most_common_value is not None:
        temp = most_common_value
    elif latest_value is not None:
        temp = latest_value
    else:
        temp = 0.0   # default fallback
    return {
        "temperature": temp, #most_common_value
        "min": -10,
        "max": 50,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }


def export_log(channel, raw, voltage):
    with open("sensor_logs.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([channel, raw, voltage])

# ლოგების კონფიგურაცია
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sensor_logs.csv", mode="a"),  # CSV ფაილში ჩაწერა
        logging.StreamHandler()  # კონსოლშიც გამოჩნდება
    ]
)



#Flask‑ის სტანდარტული werkzeug ლოგებიის შეზღუდვა
logging.getLogger("werkzeug").setLevel(logging.WARNING)

#app = Flask(__name__)
app = Flask(__name__, static_folder="static", template_folder="templates")

sensor_value = 42



    
@app.route("/")
def index():
     return render_template(
        "index.html",
        value=latest_value,
        timestamp=datetime.datetime.now().strftime("%H:%M:%S")
    )

@app.route("/ui")
def ui():
    return "<h1>Analog Sensor UI</h1><p>Sensor value endpoint: /data</p>"

@app.route("/register_service")
def register_service():
    return {
        "name": "Analog Sensor",
        "category": "services",
        "description": "ADS1115 Analog Sensor Reader",
        "version": "1.0.0",
        "new_page": True,
        "webpage": "/static/index.html"
    }


@app.route("/docs")
def docs():
    return "No docs available"


@app.route("/log", methods=["POST"])
def save_log():
    #logging.info(f"Latest value: {latest_value}")
    return jsonify({"status": "saved"})



@app.route("/settings", methods=["POST"])
def settings():
    data = request.json
    refresh_interval = data.get("refreshInterval", 5)
    return jsonify({"status": "saved", "refreshInterval": refresh_interval})


@app.route("/export")
def export_logs():
    return send_file("sensor_logs.csv", as_attachment=True)

@app.route("/data", methods=["GET"])
def get_data():
    recent_values = values[-20:]   # ბოლო 20
    #values.clear()
    labels = [datetime.datetime.now().strftime("%H:%M:%S")] * len(recent_values)
    return jsonify({
        "labels": labels,
        "values": recent_values
    })



@app.route("/data", methods=["POST"])
def set_data():
    """Update sensor value manually"""
    global sensor_value
    payload = request.get_json(force=True)
    sensor_value = payload.get("value", sensor_value)
    #logging.info(f"AnalogSensor value updated via POST: {sensor_value}")
    return jsonify({"status": "ok", "new_value": sensor_value})


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "running", "port": 5437})
    

@app.route("/docs.json")
def docs_json():
    return {"info": "No docs.json available"}, 200


@app.route("/api/sensor")
def sensor_api():
    # აირჩიე მნიშვნელობა პრიორიტეტით: most_common_value → latest_value → 0.0
    if most_common_value is not None:
        temp = most_common_value
    elif latest_value is not None:
        temp = latest_value
    else:
        temp = 0.0   # default fallback
    return jsonify({
        "temperature": temp,
        "min": -10,
        "max": 50,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })

@app.route("/openapi.json")
def openapi_json():
    return {"info": "No openapi.json available"}, 200

@app.route("/swagger.json")
def swagger_json():
    return {"info": "No swagger.json available"}, 200



def log_loop():
    global latest_value
    while True:
        try:
            for i in range(10):
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print("Received:", line, flush=True)
                    try:
                        latest_value = float(line)
                        values.append(latest_value)
                        # შეინახე მხოლოდ ბოლო 100 მნიშვნელობა
                        if len(values) > 50:
                            values.pop(0)
                    except:
                        latest_value = None

            # დაითვალე რამდენჯერ რა მნიშვნელობა გამოჩნდა
            counts = Counter(values)
            if counts:
                most_common_value = counts.most_common(1)[0][0]
            else:
                # თუ history ცარიელია, დატოვე ძველი მნიშვნელობა
                pass

            logging.info(f"Received sensor value: {most_common_value}")
            export_log("CH1", latest_value, most_common_value)
            

        except Exception as e:
            time.sleep(1)


# modbus interface 

# Modbus RTU Slave (Server)

store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*100),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*100),
    ir=ModbusSequentialDataBlock(0, [0]*100)
)
context = ModbusServerContext(slaves=store, single=True)

StartSerialServer(
    context=context,
    port='/dev/ttyUSB1',   # adjust for your adapter
    framer=FramerType.RTU,
    baudrate=9600
)
# ////////////////////////////////////////////

# Modbus RTU Master (Client)
client = ModbusSerialClient(
    port='/dev/ttyUSB1',
    framer=FramerType.RTU,
    baudrate=9600,
    timeout=3
)

if client.connect():
    SLAVE_ID = 1
    REGISTER_ADDRESS = 0
    response = client.read_holding_registers(REGISTER_ADDRESS, 5, slave=SLAVE_ID)
    print(response.registers)
else:
    print("Connection failed")

# //////////////////////////


if __name__ == "__main__":
    # პარალელურად ვუშვებთ ლოგების loop‑ს
    t = threading.Thread(target=log_loop, daemon=True)
    t.start()

    # Flask API
    app.run(host="0.0.0.0", port=5437 , debug=True)

