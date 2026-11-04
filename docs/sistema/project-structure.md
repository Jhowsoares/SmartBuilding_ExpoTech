# 📂 Estrutura do Projeto e Organização de Módulos

Este documento descreve a árvore de diretórios, a responsabilidade das camadas e a orquestração de serviços do ecossistema **Smart Building**.

---

## 🌳 Árvore de Diretórios Principal

```text
SmartBuilding/
├── backend/                 # FastAPI REST API + Python ML + MQTT Ingestion
│   ├── app/api/v1/          # Endpoints REST (Auth, Rooms, Sensors, Devices...)
│   ├── app/core/            # Configurações, Segurança (JWT/bcrypt), Exceções
│   ├── app/db/              # Sessão assíncrona SQLAlchemy + Migrações Alembic
│   ├── app/ml/              # Motor de Regras (RN01-RN10) + Regressão RandomForest
│   ├── app/models/          # Entidades ORM (Users, Rooms, Telemetry, Audits)
│   ├── app/mqtt/            # Cliente Mosquitto Paho + Handlers Asyncio
│   ├── alembic/             # Histórico de Migrações de Banco de Dados
│   └── scripts/seed_db.py   # Script de Povoamento Inicial de Dados
├── frontend/                # Single Page Application (React 18 + Vite + Tailwind CSS)
│   └── src/pages/           # Dashboard, Gestão de Salas, Métricas e Alertas
├── simulator/               # Container simulador de telemetria IoT (14 salas)
├── firmware/                # Sketches C++ para microcontroladores ESP32 (.ino)
├── tools/                   # Scripts auxiliares (Ponte Bluetooth Serial `bt_bridge.py`)
├── mosquitto/               # Arquivos de configuração do Broker MQTT
├── docs/                    # Documentação técnica e manuais de execução
├── docker-compose.yml       # Orquestração do ambiente multi-container
└── README.md                # Guia e índice principal do repositório

```

---

## 🐳 Serviços Orquestrados via Docker

| Container Docker | Serviço / Imagem Base | Função na Arquitetura | Porta Interna | Porta Exposta |
| --- | --- | --- | --- | --- |
| `sb_frontend` | React (Nginx) | Interface Gráfica do Usuário (Dashboard) | `80` | `3000` |
| `sb_backend` | FastAPI (Python 3.11) | REST API, Ingestão MQTT e Motor ML | `8000` | `8000` |
| `sb_postgres` | PostgreSQL 15 | Banco de dados relacional (Persistência) | `5432` | `5432` |
| `sb_redis` | Redis 7 | Cache de leituras e Blacklist de tokens JWT | `6379` | `6379` |
| `sb_mqtt` | Eclipse Mosquitto | Broker de Mensageria Pub/Sub IoT | `1883` / `9001` | `1883` |
| `sb_simulator` | Python Service | Gerador de telemetria sintética (14 salas) | Interno | N/A |
| `sb_ngrok` | Ngrok Tunnel | Expositor de porta local para nós físicos (Opcional) | `4040` | `4040` |

---

## 🛡️ Diretrizes de Ignoração no Versionamento (`.gitignore`)

Para garantir um repositório enxuto e seguro, as seguintes categorias de arquivos não são versionadas:

* **Dependências & Build:** `node_modules/`, `dist/`, `__pycache__/`, `.venv/`.
* **Variáveis Sensíveis:** Arquivos `.env` de cada módulo.
* **Artefatos de ML:** Modelos compilados `*.pkl` (gerados via pipeline de treino local ou endpoint `/predictions/train`).
* **Volumes de Persistência Local:** Diretores de dados do banco e cache (`postgres_data/`, `redis_data/`).

> Para maiores detalhes sobre higienização e manutenção de artefatos no Git, consulte o Guia de Manutenção do Repositório.