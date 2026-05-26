# Arquitetura e Fluxo de Dados

## Visão geral

O **Smart Building** monitora e controla climatização em edifícios corporativos. Sensores publicam leituras via MQTT; o backend aplica regras de negócio (RN01–RN10), persiste dados e expõe uma API REST; o frontend React exibe dashboards e controles.

```
Alguém sai da sala por 15 minutos?
  → Sensor de presença detecta ausência
  → RN01 ativada
  → AC desligado via MQTT
  → Ação registrada na auditoria
  → Dashboard atualiza
```

## Stack tecnológico

| Camada | Tecnologia | Motivo |
|--------|------------|--------|
| Frontend | React 18 + Vite + Tailwind + Recharts | SPA reativa, gráficos em tempo real |
| Backend | FastAPI 3.11 + Pydantic v2 | Async, docs automáticas, validação |
| Banco | PostgreSQL 15 + SQLAlchemy 2 + Alembic | ACID, migrations |
| Cache | Redis 7 | Blacklist JWT + cache |
| IoT | Mosquitto MQTT 2 | Protocolo leve para embarcados |
| ML | scikit-learn RandomForest | Predição 24h |
| Auth | JWT + bcrypt + Redis blacklist | RBAC 3 papéis, logout real |
| Infra | Docker Compose | Um comando sobe tudo |

## Diagrama do sistema

```
╔══════════════════════════════════════════════════════════════════════╗
║                        HARDWARE / BORDA IoT                          ║
║  ESP32 + BME280 / HC-SR501          Simulador Docker (14 salas)       ║
╚═══════════════╪══════════════════════════════════╪═══════════════════╝
                │ MQTT publish                       │
                ▼                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                   MOSQUITTO BROKER  :1883                             ║
╚═══════════════════════╦═══════════════════════════════════════════════╝
                        │ subscribe
                        ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                    FASTAPI BACKEND  :8000                             ║
║  MQTT Handler → Business Rules RN01-RN10 → SQLAlchemy → PostgreSQL   ║
║                                              Redis (JWT blacklist)    ║
╚═══════════════════════════════════════╦═══════════════════════════════╝
                                        │ HTTP + JWT
                                        ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                    REACT FRONTEND  :3000                              ║
╚═══════════════════════════════════════════════════════════════════════╝
```

Documentação visual interativa: [GitHub Pages](https://jhowsoares.github.io/SmartBuilding_ExpoTech/)

## Caminho do dado (temperatura)

1. **Sensor** publica em `sensors/room/room-101/temperature` com JSON `{"value": 24.3, ...}`.
2. **Mosquitto** repassa ao backend (wildcard `sensors/room/+/temperature`).
3. **MQTT Handler** (`handlers.py`) usa `asyncio.run_coroutine_threadsafe` para bridge thread-safe com asyncpg.
4. **Business Rules Engine** avalia RN01–RN10 com `RuleContext`.
5. **PostgreSQL** persiste `sensor_data`, `commands`, `alerts`.
6. **REST API** serve via `GET /api/v1/sensors/{id}/data`.
7. **React** atualiza gráficos (polling ~60s).

## Para que serve o Redis?

**1. Blacklist JWT (logout real)** — sem Redis, token revogado continua válido até expirar.

**2. Cache de leituras** — endpoints consultados frequentemente podem ser servidos do Redis, aliviando o PostgreSQL.

## Por que monorrepositório?

| Vantagem | Impacto |
|----------|---------|
| Contexto único na IDE | Autocomplete cruza frontend e backend |
| Um `docker compose up` | Qualquer integrante sobe tudo em minutos |
| CI/CD simples | Pipeline único |
| Rastreabilidade | Um commit pode cobrir API + UI + testes |
