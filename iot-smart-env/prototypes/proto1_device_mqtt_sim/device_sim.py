import os
import json
import time
import random
import argparse
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

try:
    # dotenv é opcional; se não estiver presente, seguimos sem .env
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

def iso_now() -> str:
    """Retorna timestamp ISO8601 UTC com milissegundos."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def rand_walk(value: float, step: float, min_v: float, max_v: float) -> float:
    """Passeio aleatório com limites."""
    v = value + random.uniform(-step, step)
    return max(min(v, max_v), min_v)

def main():
    parser = argparse.ArgumentParser(description="MQTT device simulator")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument("--topic", default=os.getenv("BASE_TOPIC", "iot/env/room1/reading"))
    parser.add_argument("--interval", type=float, default=float(os.getenv("PUBLISH_INTERVAL", "2")))
    parser.add_argument("--node", default=os.getenv("NODE_ID", "envnode-sim-01"))
    args = parser.parse_args()

    client = mqtt.Client(client_id=f"{args.node}-{random.randint(1000,9999)}", clean_session=True)
    client.will_set(f"{args.topic}/status", payload="offline", qos=1, retain=True)

    def on_connect(c, userdata, flags, rc):
        print(f"[SIM] Conectado ao MQTT rc={rc}")
        c.publish(f"{args.topic}/status", payload="online", qos=1, retain=True)

    client.on_connect = on_connect

    print(f"[SIM] Conectando em mqtt://{args.host}:{args.port}")
    client.connect(args.host, args.port, keepalive=30)
    client.loop_start()

    temp = 24.0
    hum = 55.0
    soil = 40.0
    fw = "proto1-sim-0.1.0"

    try:
        while True:
            temp = rand_walk(temp, 0.3, 18.0, 35.0)
            hum = rand_walk(hum, 1.2, 30.0, 90.0)
            soil = rand_walk(soil, 1.5, 10.0, 90.0)
            motion_state = random.random() < 0.1  # 10% de chance

            payload = {
                "node_id": args.node,
                "temperature_c": round(temp, 2),
                "humidity_pct": round(hum, 2),
                "soil_moisture_pct": round(soil, 2),
                "motion": motion_state,
                "timestamp": iso_now(),
                "firmware": fw
            }
            client.publish(args.topic, json.dumps(payload), qos=0, retain=False)
            print(f"[SIM] -> {args.topic} {payload}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[SIM] Encerrando...")
    finally:
        try:
            client.publish(f"{args.topic}/status", payload="offline", qos=1, retain=True)
        except Exception:
            pass
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
