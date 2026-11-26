from flask import Flask, jsonify, render_template, send_from_directory, Response
from flask import request
from collections import deque
from flask import send_file
from pymavlink import mavutil
import threading
import os
import random
import datetime
import time, threading
import logging
import math
import serial
from collections import Counter
import csv
from pymodbus.client import ModbusSerialClient



values = []
result_array = []

latest_value = None
Ph_data = None
min_value = None
max_value = None
most_common_value = None   # <-- add this line

if not os.path.exists(
    "nke_sensor_logs.csv"
):

    with open(
        "nke_sensor_logs.csv",
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([

            "Timestamp",

            "BarometricPressure",

            "Temperature",

            "pH",

            "ORP",

            "Conductivity",

            "Conductivity20",

            "Conductivity25",

            "Salinity",

            "DO_mg_L",

            "DO_Percent",

            "Depth_cm",

            "Chlorophyll",

            "GPS_Lat",

            "GPS_Lon",

            "GPS_Alt",

            "Roll",

            "Pitch",

            "Yaw"
        ])

client = ModbusSerialClient(
        port="/dev/ttyUSB0",
        baudrate=19200,
        parity="E",
        stopbits=1,
        bytesize=8,
        timeout=1
    )
client.connect()



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
    with open("nke_sensor_logs.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([channel, raw, voltage])

# ლოგების კონფიგურაცია
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)



#Flask‑ის სტანდარტული werkzeug ლოგებიის შეზღუდვა
logging.getLogger("werkzeug").setLevel(logging.WARNING)

#app = Flask(__name__)
app = Flask(__name__, static_folder="static", template_folder="templates")


master = mavutil.mavlink_connection(
    'udpin:0.0.0.0:14600'
)

latest_attitude = {}
latest_gps = {}

def mavlink_loop():
    global latest_attitude, latest_gps
    try:
        master.wait_heartbeat(timeout=10)
        print("Heartbeat OK")
    except Exception as e:
        print("Heartbeat Timeout:", e)
        print("Heartbeat OK")

    while True:
        msg = master.recv_match(blocking=True)
        if not msg:
            continue

        if msg.get_type() == "ATTITUDE":
            latest_attitude = {
                "roll": msg.roll,
                "pitch": msg.pitch,
                "yaw": msg.yaw
            }
        elif msg.get_type() == "GPS_RAW_INT":
            latest_gps = {
                "lat": msg.lat/1e7,
                "lon": msg.lon/1e7,
                "alt": msg.alt/1000.0
            }
            print("GPS:", latest_gps)
            logging.info(f"GPS Data: {latest_gps}"
            )
        
        
@app.route("/mavlink/attitude")
def attitude():
    return jsonify(latest_attitude)

@app.route("/mavlink/gps")
def gps():
    return jsonify(latest_gps)


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
        "webpage": "/static/index.html",
        "port": 5537
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
    return send_file("nke_sensor_logs.csv", as_attachment=True)

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
    return jsonify({"status": "running", "port": 5537})
    

@app.route("/docs.json")
def docs_json():
    return {"info": "No docs.json available"}, 200


@app.route("/api/sensor")
def sensor_api():

    return jsonify({
        "barometric_pressure": result_array[0] if len(result_array) > 0 else 0,
        "temperature": latest_value if latest_value is not None else 0,
        "salinity": result_array[13] / 100 if len(result_array) > 13 else 0,
        "registers": result_array,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })


@app.route("/openapi.json")
def openapi_json():
    return {"info": "No openapi.json available"}, 200

@app.route("/swagger.json")
def swagger_json():
    return {"info": "No swagger.json available"}, 200


@app.route("/modbus/data")
def modbus_data():
    global result_array 

    if len(result_array) < 5:
        return jsonify({
            "status": "waiting_for_data",
            "raw": result_array
        })

    return jsonify({
        "barometric_pressure": result_array[0],
        "temperature": result_array[1] / 100,
        "ph": result_array[2] / 100,
        "orp": result_array[3] / 10,
        "turbidity": result_array[4] / 10,

        "conductivity": (result_array[5] << 16) | result_array[6],
        "conductivity20": (result_array[7] << 16) | result_array[8],
        "conductivity25": (result_array[9] << 16) | result_array[10],

        "salinity": result_array[13] / 100,

        "dissolved_oxygen_mg_l": result_array[17] / 100,
        "dissolved_oxygen_percent": result_array[18] / 10,

        "depth_cm": result_array[19],

        "chlorophyll": (result_array[20] << 16) | result_array[21],

        "raw": result_array
    })



def test_modbus():

    global result_array
    global latest_value    
    global Ph_data

    #if client.connect():

        #logging.info("✅ kavshiri damyarda")

    result = client.read_input_registers(
        address=0,
        count=24,
        slave=1
    )

    if not result.isError():

        result_array = result.registers

        if len(result.registers) > 1:
            latest_value = result.registers[1] / 100.0
            Ph_data = result.registers[2] / 100.0           # pH

        logging.info(
            f"📊 migebuli monacemebi: {result.registers}"
        )

        barometric_pressure = result_array[0]

        temperature = result_array[1] / 100.0

        ph = result_array[2] / 100.0

        orp = result_array[3] / 10.0

        conductivity = (
            (result_array[5] << 16)
            | result_array[6]
        )

        conductivity20 = (
            (result_array[7] << 16)
            | result_array[8]
        )

        conductivity25 = (
            (result_array[9] << 16)
            | result_array[10]
        )

        salinity = result_array[13] / 100.0

        do_mg_l = (
            result_array[17] / 100.0
        )

        do_percent = (
            result_array[18] / 10.0
        )

        depth_cm = result_array[19]

        chlorophyll = (
            (result_array[20] << 16)
            | result_array[21]
        )

        gps_lat = latest_gps.get(
            "lat",
            0
        )

        gps_lon = latest_gps.get(
            "lon",
            0
        )

        gps_alt = latest_gps.get(
            "alt",
            0
        )

        roll = latest_attitude.get(
            "roll",
            0
        )

        pitch = latest_attitude.get(
            "pitch",
            0
        )

        yaw = latest_attitude.get(
            "yaw",
            0
        )

        with open(
            "nke_sensor_logs.csv",
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([

                datetime.datetime.now()
                .strftime("%Y-%m-%d %H:%M:%S"),

                barometric_pressure,

                temperature,

                ph,

                orp,

                conductivity,
                conductivity20,
                conductivity25,
                salinity,
                
                do_mg_l,
                do_percent,

                depth_cm,

                chlorophyll,

                gps_lat,
                gps_lon,
                gps_alt,

                roll,
                pitch,
                yaw
            ])
        #else:

            #logging.warning(
            #    f"Modbus Error: {result}"
            #)

        #client.close()

   # else:

        #logging.info(
       #     "❌ ver moxerxda kavshiris damyareba"
       # )



def log_loop():
    global  most_common_value
    while True:
        try:
            #pass
            #time.sleep(1)
            # თუ გინდა Modbus მონაცემების კითხვა, გააქტიურე ეს:
            # data = read_modbus_data(
            #     port="/dev/ttyUSB0",
            #     baudrate=19200,
            #     slave_id=1,
            #     address=1,
            #     count=4
            # )

            # logging.info(f"Received sensor value: {data}")

            # history‑დან ყველაზე ხშირი მნიშვნელობის პოვნა
            #counts = Counter(values)
            #if counts:
            #    most_common_value = counts.most_common(1)[0][0]

            #export_log("CH1", latest_value or 0, most_common_value or 0)
            test_modbus()
            time.sleep(3)
        except Exception as e:
            logging.error(f"Error in log_loop: {e}")
            time.sleep(1)




if __name__ == "__main__":
    
    # Thread 1
    threading.Thread(target=mavlink_loop, daemon=True).start()

    # Thread 2
    # პარალელურად ვუშვებთ ლოგების loop‑ს
    t = threading.Thread(target=log_loop, daemon=True)
    t.start()  

    # Flask API
    app.run(host="0.0.0.0", port=5537 , debug=False)


