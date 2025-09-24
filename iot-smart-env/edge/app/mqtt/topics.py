"""
Convenções de tópico MQTT usadas no projeto.
"""

from __future__ import annotations

READING_DEFAULT = "iot/env/room1/reading"
READING_WILDCARD = "iot/+/+/reading"  # usado por padrão no EDGE

STATUS_SUFFIX = "status"  # ex.: iot/env/room1/reading/status


def is_status_topic(topic: str) -> bool:
    return topic.strip().endswith("/" + STATUS_SUFFIX)
