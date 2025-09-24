import os
import json
import queue
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

import paho.mqtt.client as mqtt

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Boolean, DateTime

# -------- Config --------
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/+/+/reading")  # wildcard por padrão
DB_URL = os.getenv("DB_URL", "sqlite:///./readings.db")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")

# -------- DB --------
class Base(DeclarativeBase):
    pass

class Reading(Base):
    __tablename__ = "readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(64), index=True)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    soil_moisture_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motion: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    raw_json: Mapped[str] = mapped_column(String, nullable=False)

engine_kwargs = {"connect_args": {"check_same_thread": False}} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, **engine_kwargs)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# -------- API --------
app = FastAPI(title="Proto2 Edge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS if ALLOW_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReadingOut(BaseModel):
    id: int
    node_id: str
    temperature_c: float | None = None
    humidity_pct: float | None = None
    soil_moisture_pct: float | None = None
    motion: bool | None = None
    timestamp: datetime

class HealthOut(BaseModel):
    status: str
    mqtt: Dict[str, Any]
    counts: Dict[str, int]
    db_url: str

# -------- WS manager --------
class WSManager:
    def __init__(self) -> None:
        self.connections: list[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        with self.lock:
            self.connections.append(ws)

    def remove(self, ws: WebSocket):
        with self.lock:
            if ws in self.connections:
                self.connections.remove(ws)

    async def broadcast_json(self, data: dict):
        to_remove = []
        for ws in list(self.connections):
            try:
                await ws.send_json(data)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.remove(ws)

ws_manager = WSManager()

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantemos a conexão viva; cliente pode enviar pings ocasionais
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.remove(websocket)

@app.get("/health", response_model=HealthOut)
def health():
    with SessionLocal() as s:
        total = s.execute(text("select count(1) from readings")).scalar_one()
        nodes = s.execute(text("select count(distinct node_id) from readings")).scalar_one()
    return HealthOut(
        status="ok",
        mqtt={"host": MQTT_HOST, "port": MQTT_PORT, "topic": MQTT_TOPIC},
        counts={"readings": int(total or 0), "nodes": int(nodes or 0)},
        db_url=DB_URL,
    )

@app.get("/readings", response_model=List[ReadingOut])
def get_readings(
    limit: int = Query(50, ge=1, le=1000),
    node_id: Optional[str] = None
):
    with SessionLocal() as s:
        q = s.query(Reading).order_by(Reading.id.desc())
        if node_id:
            q = q.filter(Reading.node_id == node_id)
        rows = q.limit(limit).all()
        rows = list(reversed(rows))  # entrega em ordem cronológica crescente
        return [
            ReadingOut(
                id=r.id,
                node_id=r.node_id,
                temperature_c=r.temperature_c,
                humidity_pct=r.humidity_pct,
                soil_moisture_pct=r.soil_moisture_pct,
                motion=r.motion,
                timestamp=r.timestamp,
            )
            for r in rows
        ]

# -------- MQTT workers --------
msg_queue: "queue.Queue[dict]" = queue.Queue()

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Conectado rc={rc}")
    client.subscribe(MQTT_TOPIC, qos=0)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        payload["_topic"] = msg.topic
        msg_queue.put(payload)
    except Exception as e:
        print("[MQTT] Payload inválido:", e)

def mqtt_worker():
    # API v2 do paho usa enum para compatibilidade
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_forever()

def db_worker():
    while True:
        payload = msg_queue.get()
        try:
            ts = payload.get("timestamp")
            try:
                ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else datetime.utcnow()
            except Exception:
                ts_dt = datetime.utcnow()
            with SessionLocal() as s:
                r = Reading(
                    node_id=payload.get("node_id", "unknown"),
                    temperature_c=payload.get("temperature_c"),
                    humidity_pct=payload.get("humidity_pct"),
                    soil_moisture_pct=payload.get("soil_moisture_pct"),
                    motion=payload.get("motion"),
                    timestamp=ts_dt,
                    raw_json=json.dumps(payload, ensure_ascii=False),
                )
                s.add(r)
                s.commit()

                # Broadcast (executado de thread): usa anyio utilitário do FastAPI
                try:
                    import anyio
                    anyio.from_thread.run(
                        ws_manager.broadcast_json,
                        {
                            "id": r.id,
                            "node_id": r.node_id,
                            "temperature_c": r.temperature_c,
                            "humidity_pct": r.humidity_pct,
                            "soil_moisture_pct": r.soil_moisture_pct,
                            "motion": r.motion,
                            "timestamp": r.timestamp.isoformat()
                        }
                    )
                except Exception as e:
                    # Se app ainda não iniciou o loop async, ignoramos
                    print("[WS] Broadcast falhou (provável app iniciando):", e)
        except Exception as e:
            print("[DB] Erro:", e)
        finally:
            msg_queue.task_done()

# Inicializa workers ao importar app
t1 = threading.Thread(target=mqtt_worker, daemon=True)
t1.start()
t2 = threading.Thread(target=db_worker, daemon=True)
t2.start()
