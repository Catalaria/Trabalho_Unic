# Proto3 — Frontend mínimo (Vite + React + Recharts)

Este protótipo consome o **WebSocket** do Proto2 (`/ws`) e exibe **gráficos em tempo real**.
Inclui uma página única com um gráfico de temperatura/umidade e informação do(s) nó(s) ativos.

## Dependências conceituais
- WebSocket: `ws://localhost:8000/ws`
- Formato das mensagens: o mesmo enviado pelo Proto2 no broadcast (JSON de leitura)

> Observação: quando concluirmos a estrutura completa do projeto, poderemos evoluir este protótipo para o dashboard final (login simulado, tema Light/Dark, filtros, etc.).
