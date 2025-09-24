"""
Configuração central do EDGE.
Lê variáveis de ambiente e expõe um objeto `settings`.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass


def _split_origins() -> List[str]:
    v = os.getenv("ALLOW_ORIGINS", "*")
    # remove espaços e ignora vazios
    out = [s.strip() for s in v.split(",") if s.strip()]
    return out or ["*"]


@dataclass
class Settings:
    # MQTT
    MQTT_HOST: str = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_TOPIC: str = os.getenv("MQTT_TOPIC", "iot/+/+/reading")  # wildcard suportado
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "edge-consumer")

    # Banco
    DB_URL: str = os.getenv("DB_URL", "sqlite:///./edge_readings.db")

    # CORS (usar default_factory para evitar lista mutável estática)
    ALLOW_ORIGINS: List[str] = field(default_factory=_split_origins)

    # Segurança “fingida” (admin)
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "admin-demo-token")


settings = Settings()
