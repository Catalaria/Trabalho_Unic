"""
Aplicação FastAPI principal do EDGE (backend local).
- Inclui rotas REST
- Gerencia WebSocket
- Inicializa workers (MQTT ingest + regras)
"""

from __future__ import annotations

import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.routes import api_router
from .ws.websocket import ws_router
from .mqtt.client import MqttWorker

app = FastAPI(title="IoT Edge Backend", version="0.1.0")

# CORS
origins = ["*"] if settings.ALLOW_ORIGINS == ["*"] else settings.ALLOW_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas REST
app.include_router(api_router, prefix="")

# WebSocket
app.include_router(ws_router, prefix="")

# MQTT Worker (singleton controlado neste módulo)
_mqtt_worker: MqttWorker | None = None
_mqtt_thread: threading.Thread | None = None


@app.on_event("startup")
def _startup():
    global _mqtt_worker, _mqtt_thread
    if _mqtt_worker is None:
        _mqtt_worker = MqttWorker(
            host=settings.MQTT_HOST,
            port=settings.MQTT_PORT,
            topic=settings.MQTT_TOPIC,
            keepalive=30,
        )
        _mqtt_thread = threading.Thread(target=_mqtt_worker.run_forever, daemon=True)
        _mqtt_thread.start()


@app.on_event("shutdown")
def _shutdown():
    global _mqtt_worker
    try:
        if _mqtt_worker:
            _mqtt_worker.stop()
    except Exception:
        pass
