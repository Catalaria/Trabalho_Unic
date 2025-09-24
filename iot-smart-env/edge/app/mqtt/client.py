"""
Cliente/worker MQTT para consumir leituras e encaminhar para o pipeline (ingest + regras + WS).
"""

from __future__ import annotations
import json
import threading
import queue
import time
import paho.mqtt.client as mqtt

from ..core.config import settings
from ..services.ingest import process_incoming_payload


class MqttWorker:
    def __init__(self, host: str, port: int, topic: str, keepalive: int = 30):
        self.host = host
        self.port = port
        self.topic = topic
        self.keepalive = keepalive
        self._stop = threading.Event()
        self._q: "queue.Queue[dict]" = queue.Queue()

        # paho API v2
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=settings.MQTT_CLIENT_ID, clean_session=True)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # paho callbacks
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[MQTT] Connected rc={rc}")
        client.subscribe(self.topic, qos=0)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            payload["_topic"] = msg.topic
            self._q.put(payload)
        except Exception as e:
            print("[MQTT] Bad payload:", e)

    # threads
    def _db_worker(self):
        while not self._stop.is_set():
            try:
                payload = self._q.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                process_incoming_payload(payload)
            except Exception as e:
                print("[INGEST] Error:", e)
            finally:
                self._q.task_done()

    def run_forever(self):
        t = threading.Thread(target=self._db_worker, daemon=True)
        t.start()
        self.client.connect(self.host, self.port, keepalive=self.keepalive)
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            pass

    def stop(self):
        self._stop.set()
        try:
            self.client.disconnect()
        except Exception:
            pass
