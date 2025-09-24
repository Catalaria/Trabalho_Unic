# Proto1 — Dispositivo Simulado (MQTT)

Este protótipo simula um nó ESP32 publicando leituras de sensores via MQTT.
Ele **não** exige hardware; serve para validar tópicos, payloads e integração com o Edge.

## Sensores simulados
- Temperatura do ar (°C)
- Umidade relativa do ar (%)
- Umidade do solo (%)
- Presença (PIR) (booleano)

## Tópico padrão
- Leituras: `iot/env/room1/reading`
- Status do nó (LWT): `iot/env/room1/reading/status` (online/offline)

## Variáveis suportadas (via `.env` ou argumentos)
- `MQTT_HOST` (default: `localhost`)
- `MQTT_PORT` (default: `1883`)
- `BASE_TOPIC` (default: `iot/env/room1/reading`)
- `NODE_ID` (default: `envnode-sim-01`)
- `PUBLISH_INTERVAL` (segundos, default: `2`)

## Formato da mensagem (JSON)
```json
{
  "node_id": "envnode-sim-01",
  "temperature_c": 24.7,
  "humidity_pct": 58.2,
  "soil_moisture_pct": 41.3,
  "motion": false,
  "timestamp": "2025-09-17T19:30:10.123Z",
  "firmware": "proto1-sim-0.1.0"
}
