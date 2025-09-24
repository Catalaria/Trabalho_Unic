"""
Canal de notificações (placeholder).
Poderia enviar webhook/discord/email. Aqui mantemos como stub para uso futuro.
"""

from __future__ import annotations


def send_webhook(url: str, payload: dict):
    # Implementação futura: requests.post(url, json=payload, timeout=3)
    # Mantido como stub para não adicionar dependências externas agora.
    return {"status": "queued", "url": url, "payload": payload}
