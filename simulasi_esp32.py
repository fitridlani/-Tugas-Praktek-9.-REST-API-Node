import paho.mqtt.client as mqtt
import json, time, random
from datetime import datetime

BROKER = "localhost"
TOPIC_SENSOR = "iot/sensor"
TOPIC_KONTROL = "iot/kontrol"
TOPIC_NOTIF = "iot/notifikasi"

lampu = "off"   # status LED simulasi (ikut dikirim ke dashboard sebagai umpan balik)


def kirim_data():
    data = {
        "suhu": round(random.uniform(25, 32), 1),
        "kelembaban": round(random.uniform(55, 80), 1),
        "lampu": lampu,
        "timestamp": datetime.now().isoformat()
    }
    client.publish(TOPIC_SENSOR, json.dumps(data))
    print(f"-> Publish: {data}")


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Terhubung ke broker (code: {reason_code})")
    client.subscribe([(TOPIC_KONTROL, 0), (TOPIC_NOTIF, 0)])


def on_message(client, userdata, msg):
    global lampu
    d = json.loads(msg.payload.decode())
    if msg.topic == TOPIC_KONTROL:
        print(f"<- KONTROL diterima: {d['device']} = {d['action'].upper()}")
        if d["device"] == "lamp":
            lampu = d["action"]
            print(f"   LED sekarang: {lampu.upper()}")
            kirim_data()   # kirim segera agar dashboard langsung menampilkan status baru
    else:
        print(f"<- NOTIFIKASI: {d.get('message')}")


# paho-mqtt v2 (sesuai catatan modul)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ESP32-Simulator")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.loop_start()

print("ESP32 Simulator berjalan... Ctrl+C untuk stop")
try:
    while True:
        kirim_data()
        time.sleep(3)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
