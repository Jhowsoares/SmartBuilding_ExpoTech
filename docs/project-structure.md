# Estrutura do Projeto

```
SmartBuilding/
├── backend/                 # FastAPI + ML + MQTT
│   ├── app/api/v1/          # Endpoints REST
│   ├── app/core/            # Config, JWT, deps, exceptions
│   ├── app/db/              # SQLAlchemy async
│   ├── app/ml/              # Regras + predictor + models/
│   ├── app/models/          # ORM (users, rooms, devices...)
│   ├── app/mqtt/            # Client + handlers
│   ├── alembic/             # Migrations
│   └── scripts/seed_db.py   # Dados iniciais
├── frontend/                # React 18 + Vite + Tailwind
│   └── src/pages/           # Dashboard, Salas, Relatórios...
├── simulator/               # 14 salas MQTT simuladas
├── firmware/                # ESP32 (.ino)
├── tools/                   # bt_bridge.py, qrcode_civil.html
├── mosquitto/               # Config broker
├── docs/                    # Documentação (esta pasta)
├── docker-compose.yml
└── README.md                # Índice principal
```

## Serviços Docker

| Container | Função |
|-----------|--------|
| `sb_frontend` | React + nginx |
| `sb_backend` | FastAPI |
| `sb_postgres` | PostgreSQL |
| `sb_redis` | Redis |
| `sb_mqtt` | Mosquitto |
| `sb_simulator` | Simulador Python |
| `sb_ngrok` | Túnel TCP (opcional) |

## Pastas ignoradas pelo Git

- `node_modules/`, `__pycache__/`, `.env`
- `*.pkl` (modelos ML)
- `postgres_data/`, `redis_data/` (volumes Docker locais)

Ver [Repositório — tamanho](./repositorio.md).
