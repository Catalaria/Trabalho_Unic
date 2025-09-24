"""
Pipeline de ingestão do EDGE.

Responsabilidades:
1) Normalizar payloads vindos do MQTT (tipos, timestamp).
2) Persistir a leitura no banco (models.Reading).
3) Disparar broadcast via WebSocket para clientes em tempo real.
4) Avaliar regras de automação após a persistência.

Compatível com os demais arquivos enviados:
- SessionLocal em ..db.db
- models em ..db.models
- ws_manager em ..ws.websocket
- evaluate_rules em .rules
- anyio listado em edge/requirements.txt
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..db.db import SessionLocal
from ..db import models
from ..ws.websocket import ws_manager
from .rules import evaluate_rules


def _parse_timestamp(ts: Any) -> datetime:
    """
    Aceita:
      - ISO 8601 (com ou sem 'Z'), ex: '2025-09-17T19:30:10.123Z'
      - datetime (retorna como está)
      - None / inválido -> agora (UTC)
    """
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            # Suporta 'Z' como UTC
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            pass
    # fallback: agora
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _coerce_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip().replace(",", "."))
        except Exception:
            return None
    return None


def _coerce_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "1", "yes", "y", "on"}:
            return True
        if s in {"false", "0", "no", "n", "off"}:
            return False
    return None


def _normalize_payload(payload: dict) -> dict:
    """
    Normaliza chaves esperadas:
    - node_id: str
    - temperature_c: float | None
    - humidity_pct: float | None
    - soil_moisture_pct: float | None
    - motion: bool | None
    - timestamp: datetime
    Mantém o payload original em raw_json.
    """
    node_id = str(payload.get("node_id", "unknown"))
    temperature_c = _coerce_float(payload.get("temperature_c"))
    humidity_pct = _coerce_float(payload.get("humidity_pct"))
    soil_moisture_pct = _coerce_float(payload.get("soil_moisture_pct"))
    motion = _coerce_bool(payload.get("motion"))
    ts_dt = _parse_timestamp(payload.get("timestamp"))

    return {
        "node_id": node_id,
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "soil_moisture_pct": soil_moisture_pct,
        "motion": motion,
        "timestamp": ts_dt,
        "raw_json": json.dumps(payload, ensure_ascii=False),
    }


def process_incoming_payload(payload: dict) -> None:
    """
    Entrada: dict vindo do callback do MQTT (já convertido de JSON).
    Efeitos:
      - Cria models.Reading
      - Commit no DB
      - Broadcast via WS
      - Avalia regras ativas
    """
    norm = _normalize_payload(payload)

    with SessionLocal() as s:
        r = models.Reading(
            node_id=norm["node_id"],
            temperature_c=norm["temperature_c"],
            humidity_pct=norm["humidity_pct"],
            soil_moisture_pct=norm["soil_moisture_pct"],
            motion=norm["motion"],
            timestamp=norm["timestamp"],
            raw_json=norm["raw_json"],
        )
        s.add(r)
        s.commit()
        s.refresh(r)

        # Broadcast WebSocket (executado a partir de uma thread -> usar anyio.from_thread.run)
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
                    "timestamp": r.timestamp.isoformat(),
                },
            )
        except Exception as e:
            # Não interrompe o pipeline se o WS falhar (ex.: app subindo)
            print("[WS] Broadcast falhou:", e)

        # Avaliar regras (log de ações, etc.)
        try:
            evaluate_rules(s, r)
        except Exception as e:
            # Não interromper ingestão por regra malformada
            print("[RULES] Avaliação falhou:", e)
