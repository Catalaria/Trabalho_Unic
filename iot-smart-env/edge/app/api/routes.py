"""
Rotas REST do EDGE:
- /health        (GET/HEAD)
- /readings      (GET, POST opcional p/ testes)
- /rules         (GET, POST, PUT, DELETE)
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.config import settings
from ..core.security import AdminDep
from ..db.db import get_session, init_db
from ..db import models

api_router = APIRouter()


# ---------- Modelos Pydantic ----------
class ReadingOut(BaseModel):
    id: int
    node_id: str
    temperature_c: float | None = None
    humidity_pct: float | None = None
    soil_moisture_pct: float | None = None
    motion: bool | None = None
    timestamp: datetime


class ReadingIn(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=120)
    temperature_c: float | None = None
    humidity_pct: float | None = None
    soil_moisture_pct: float | None = None
    motion: bool | None = None
    # se não vier timestamp, usamos "agora" (UTC) no backend
    timestamp: Optional[datetime] = None


class HealthOut(BaseModel):
    status: str
    mqtt: dict
    counts: dict
    db_url: str


class RuleIn(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    enabled: bool = True
    metric: str = Field(..., pattern="^(temperature_c|humidity_pct|soil_moisture_pct)$")
    operator: str = Field(..., pattern="^(<|<=|>|>=|==|!=)$")
    value: float
    action: str = Field(..., pattern="^(notify|irrigation_on)$")
    action_params: dict | None = None


class RuleOut(RuleIn):
    id: int
    created_at: datetime
    updated_at: datetime


# ---------- Inicialização do DB (uma vez) ----------
init_db()


# ---------- Endpoints ----------
@api_router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_session)):
    try:
        total = db.execute(text("select count(1) from readings")).scalar_one()
        nodes = db.execute(
            text("select count(distinct node_id) from readings")
        ).scalar_one()
        status = "ok"
    except Exception:
        # Em caso de falha pontual de DB, não derruba a rota
        total = 0
        nodes = 0
        status = "degraded"
    return HealthOut(
        status=status,
        mqtt={
            "host": settings.MQTT_HOST,
            "port": settings.MQTT_PORT,
            "topic": settings.MQTT_TOPIC,
        },
        counts={"readings": int(total or 0), "nodes": int(nodes or 0)},
        db_url=settings.DB_URL,
    )


@api_router.head("/health", include_in_schema=False)
def health_head():
    # Responde 200 para check rápido (sem corpo)
    return Response(status_code=200)


@api_router.get("/readings", response_model=List[ReadingOut])
def get_readings(
    limit: int = Query(100, ge=1, le=5000),
    node_id: Optional[str] = None,
    since: Optional[str] = None,  # ISO 8601
    until: Optional[str] = None,  # ISO 8601
    db: Session = Depends(get_session),
):
    q = db.query(models.Reading)
    if node_id:
        q = q.filter(models.Reading.node_id == node_id)
    if since:
        try:
            d = datetime.fromisoformat(since.replace("Z", "+00:00"))
            q = q.filter(models.Reading.timestamp >= d)
        except Exception:
            pass
    if until:
        try:
            d = datetime.fromisoformat(until.replace("Z", "+00:00"))
            q = q.filter(models.Reading.timestamp <= d)
        except Exception:
            pass
    q = q.order_by(models.Reading.id.desc()).limit(limit)
    rows = list(reversed(q.all()))
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


@api_router.post("/readings", response_model=ReadingOut, dependencies=[AdminDep])
def create_reading(body: ReadingIn, db: Session = Depends(get_session)):
    """Endpoint opcional para testes manuais sem MQTT."""
    ts = body.timestamp or datetime.utcnow()
    r = models.Reading(
        node_id=body.node_id,
        temperature_c=body.temperature_c,
        humidity_pct=body.humidity_pct,
        soil_moisture_pct=body.soil_moisture_pct,
        motion=body.motion,
        timestamp=ts,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return ReadingOut(
        id=r.id,
        node_id=r.node_id,
        temperature_c=r.temperature_c,
        humidity_pct=r.humidity_pct,
        soil_moisture_pct=r.soil_moisture_pct,
        motion=r.motion,
        timestamp=r.timestamp,
    )


@api_router.get("/rules", response_model=List[RuleOut])
def list_rules(db: Session = Depends(get_session)):
    rules = db.query(models.Rule).order_by(models.Rule.id.asc()).all()
    return [
        RuleOut(
            id=r.id,
            name=r.name,
            enabled=r.enabled,
            metric=r.metric,
            operator=r.operator,
            value=r.value,
            action=r.action,
            action_params=r.action_params,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rules
    ]


@api_router.post("/rules", response_model=RuleOut, dependencies=[AdminDep])
def create_rule(body: RuleIn, db: Session = Depends(get_session)):
    if db.query(models.Rule).filter(models.Rule.name == body.name).first():
        raise HTTPException(status_code=400, detail="Nome de regra já existe.")
    r = models.Rule(
        name=body.name,
        enabled=body.enabled,
        metric=body.metric,
        operator=body.operator,
        value=body.value,
        action=body.action,
        action_params=body.action_params or {},
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return RuleOut(
        id=r.id,
        name=r.name,
        enabled=r.enabled,
        metric=r.metric,
        operator=r.operator,
        value=r.value,
        action=r.action,
        action_params=r.action_params,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@api_router.put("/rules/{rule_id}", response_model=RuleOut, dependencies=[AdminDep])
def update_rule(rule_id: int, body: RuleIn, db: Session = Depends(get_session)):
    r = db.query(models.Rule).filter(models.Rule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    r.name = body.name
    r.enabled = body.enabled
    r.metric = body.metric
    r.operator = body.operator
    r.value = body.value
    r.action = body.action
    r.action_params = body.action_params or {}
    db.commit()
    db.refresh(r)
    return RuleOut(
        id=r.id,
        name=r.name,
        enabled=r.enabled,
        metric=r.metric,
        operator=r.operator,
        value=r.value,
        action=r.action,
        action_params=r.action_params,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@api_router.delete("/rules/{rule_id}", dependencies=[AdminDep])
def delete_rule(rule_id: int, db: Session = Depends(get_session)):
    r = db.query(models.Rule).filter(models.Rule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    db.delete(r)
    db.commit()
    return {"status": "deleted", "id": rule_id}
