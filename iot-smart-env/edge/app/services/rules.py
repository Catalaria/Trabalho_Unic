"""
Motor simples de regras:
- Suporta regra de limiar (metric operator value)
- Ações: "notify" (logar) e "irrigation_on" (simulada: loga ação + params)
"""

from __future__ import annotations
from typing import Callable
from sqlalchemy.orm import Session
from ..db import models


_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">":  lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _get_metric_value(reading: models.Reading, metric: str) -> float | None:
    if metric == "temperature_c":
        return reading.temperature_c
    if metric == "humidity_pct":
        return reading.humidity_pct
    if metric == "soil_moisture_pct":
        return reading.soil_moisture_pct
    return None


def _log_action(s: Session, rule: models.Rule, reading: models.Reading, action: str, payload: dict | None = None):
    log = models.ActionLog(
        rule_id=rule.id if rule else None,
        reading_id=reading.id if reading else None,
        action=action,
        payload=payload or {},
    )
    s.add(log)
    s.commit()


def _do_notify(s: Session, rule: models.Rule, reading: models.Reading):
    _log_action(s, rule, reading, action="notify", payload={"msg": f"Rule '{rule.name}' matched"})


def _do_irrigation_on(s: Session, rule: models.Rule, reading: models.Reading):
    duration =  int((rule.action_params or {}).get("duration_sec", 15))
    zone =       (rule.action_params or {}).get("zone", "A")
    _log_action(
        s, rule, reading,
        action="irrigation_on",
        payload={"duration_sec": duration, "zone": zone, "node_id": reading.node_id}
    )


_ACTIONS = {
    "notify": _do_notify,
    "irrigation_on": _do_irrigation_on,
}


def evaluate_rules(s: Session, reading: models.Reading):
    rules = s.query(models.Rule).filter(models.Rule.enabled == True).all()  # noqa: E712
    for rule in rules:
        metric_val = _get_metric_value(reading, rule.metric)
        if metric_val is None:
            continue
        op = _OPERATORS.get(rule.operator)
        if not op:
            continue
        try:
            if op(float(metric_val), float(rule.value)):
                action_fn = _ACTIONS.get(rule.action)
                if action_fn:
                    action_fn(s, rule, reading)
        except Exception:
            # Não derruba o pipeline por causa de uma regra malformada
            pass
