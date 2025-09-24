# Proto2 — Edge mínimo (FastAPI + MQTT + SQLite + WebSocket)

Este protótipo:
- **Assina** mensagens em tópicos MQTT (leituras do Proto1 ou de um ESP32 real).
- **Persiste** no SQLite.
- **Expõe** REST para consulta e **WebSocket** para stream em tempo real.

## Endpoints
- `GET /health` — estado do banco e do MQTT.
- `GET /readings?limit=50&node_id=...` — últimas leituras.
- `WS  /ws` — cada leitura nova em JSON.

## Variáveis de ambiente esperadas
- `MQTT_HOST` (default: `localhost`)
- `MQTT_PORT` (default: `1883`)
- `MQTT_TOPIC` (default: `iot/+/+/reading`) — suporta wildcard
- `DB_URL` (default: `sqlite:///./readings.db`)
- `ALLOW_ORIGINS` (default: `*`)

> Observação: este README documenta a interface e configuração. A execução pode ser feita após concluirmos o preenchimento de todos os arquivos do projeto.
