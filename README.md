# 🏢 Smart Building — Sistema de Controle Inteligente de Ar-Condicionado

> Projeto ExpoTech — Engenharia da Computação | Período: 19–31 Maio 2026

Sistema IoT para monitoramento e controle inteligente de climatização, com backend FastAPI, dashboard React, MQTT, PostgreSQL e predições por Machine Learning.

---

## 📋 Sumário

- [Arquitetura](#arquitetura)
- [Stack Tecnológico](#stack-tecnológico)
- [Pré-requisitos](#pré-requisitos)
- [Setup Local (5 minutos)](#setup-local)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Comandos Úteis](#comandos-úteis)
- [API — Endpoints Principais](#api)
- [Credenciais de Acesso](#credenciais)
- [Estrutura do Projeto](#estrutura)
- [Equipe](#equipe)

---

## Arquitetura

```
[Simulador MQTT / ESP32]
         │
         ▼ MQTT (paho)
[Mosquitto Broker :1883]
         │
         ▼ subscribe
[FastAPI Backend :8000] ──── JWT Auth ──── [React Frontend :3000]
         │                                       │
    [PostgreSQL :5432]              Dashboard + Controle + Alertas
    [Redis :6379]
         │
    [ML (scikit-learn)]
    predição de consumo 24h
```

---

## Stack Tecnológico

| Camada | Tecnologia |
|--------|------------|
| Frontend | React 18 + Vite + TailwindCSS + Recharts |
| Backend | FastAPI (Python 3.11) + SQLAlchemy 2.0 |
| Banco de Dados | PostgreSQL 15 |
| Cache / Blacklist | Redis 7 |
| Mensageria IoT | Mosquitto 2 (MQTT) |
| IA/ML | scikit-learn (RandomForest + LinearRegression) |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Infraestrutura | Docker Compose |
| Exposição externa | ngrok |

---

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x
- [Git](https://git-scm.com/)

> ⚠️ Não é necessário Python, Node.js ou qualquer outra dependência local.

---

## Setup Local

```bash
# 1. Clone o repositório
git clone <url-do-repo>
cd SmartBuilding

# 2. Copie as variáveis de ambiente
cp backend/.env.example backend/.env

# 3. Suba todos os serviços
docker compose up -d --build

# 4. Aguarde o backend iniciar (~30s) e verifique os logs
docker compose logs -f backend
# Aguarde: "Smart Building API v1.0.0 iniciando"

# 5. O banco é migrado e populado automaticamente na primeira inicialização
# Para executar manualmente se necessário:
docker compose exec backend sh -c "cd /app && alembic upgrade head"
docker compose exec backend python scripts/seed_db.py
```

### Verificar se está tudo funcionando

```bash
# Health check da API
curl http://localhost:8000/api/v1/health

# Swagger UI (documentação interativa)
open http://localhost:8000/api/docs

# Frontend
open http://localhost:3000
```

---

## Variáveis de Ambiente

Arquivo: `backend/.env` (copiar de `.env.example`)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL asyncpg do PostgreSQL | `postgresql+asyncpg://...` |
| `SYNC_DATABASE_URL` | URL psycopg2 para Alembic | `postgresql+psycopg2://...` |
| `JWT_SECRET` | Segredo JWT (mín. 32 chars) | alterar em produção |
| `REDIS_URL` | URL do Redis | `redis://redis:6379/0` |
| `MQTT_BROKER` | Host do broker MQTT | `mqtt` |
| `MQTT_PORT` | Porta MQTT | `1883` |
| `CORS_ORIGINS` | Origens permitidas | `*` (dev) |
| `ENERGIA_TARIFA_KWH_BRL` | Tarifa kWh em R$ | `0.75` |

---

## Comandos Úteis

```bash
# Ver logs de um serviço específico
docker compose logs -f backend
docker compose logs -f simulator
docker compose logs -f mqtt

# Reiniciar o backend após alterações no código
docker compose restart backend

# Acessar shell do backend
docker compose exec backend bash

# Rodar migrations manualmente
docker compose exec backend sh -c "cd /app && alembic upgrade head"

# Criar nova migration
docker compose exec backend sh -c "cd /app && alembic revision --autogenerate -m 'descricao'"

# Retreinar modelo de ML via API
curl -X POST http://localhost:8000/api/v1/predictions/train \
  -H "Authorization: Bearer <token>"

# Derrubar tudo e limpar volumes
docker compose down -v

# Subir apenas infraestrutura (sem backend/frontend)
docker compose up -d postgres redis mqtt
```

---

## API — Endpoints Principais

Base URL: `http://localhost:8000/api/v1`

### Autenticação
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/auth/login` | Login, retorna JWT |
| `POST` | `/auth/refresh` | Renovar access token |
| `POST` | `/auth/logout` | Revogar token |

### Sensores
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/sensors` | Listar sensores |
| `POST` | `/sensors/data` | Ingerir leitura |
| `GET` | `/sensors/{id}/latest` | Última leitura |
| `GET` | `/sensors/{id}/data?period=24h` | Histórico |

### Dispositivos
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/devices` | Listar ACs e sensores |
| `POST` | `/devices` | Cadastrar dispositivo |
| `POST` | `/devices/{id}/control` | Ligar/Desligar/Setpoint |
| `GET` | `/devices/{id}/status` | Status atual |

### Alertas
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/alerts?active_only=true` | Alertas ativos |
| `POST` | `/alerts/{id}/acknowledge` | Reconhecer |
| `POST` | `/alerts/{id}/resolve` | Resolver |
| `GET` | `/alerts/history?days=30` | Histórico |

### Consumo e Predições
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/consumption?period=24h` | Histórico de consumo |
| `GET` | `/consumption/summary` | Resumo por sala |
| `GET` | `/predictions/24h` | Predição próximas 24h |
| `POST` | `/predictions/train` | Retreinar modelo ML |

---

## Credenciais

| Usuário | Senha | Papel |
|---------|-------|-------|
| `admin@smartbuilding.local` | `admin123` | admin (acesso total) |
| `operador@smartbuilding.local` | `op123` | operador (controle + alertas) |
| `visualizador@smartbuilding.local` | `view123` | visualizador (somente leitura) |

---

## Estrutura

```
SmartBuilding/
├── backend/                    # FastAPI + ML
│   ├── app/
│   │   ├── api/v1/             # Endpoints REST
│   │   ├── core/               # Config, JWT, Exceções
│   │   ├── db/                 # SQLAlchemy, sessions
│   │   ├── ml/                 # Predições + Regras de Negócio
│   │   │   ├── features.py     # Pipeline de features
│   │   │   ├── predictor.py    # Modelo RandomForest
│   │   │   └── business_rules.py  # RN01-RN10
│   │   ├── models/             # ORM (8 tabelas)
│   │   ├── mqtt/               # Cliente MQTT + handlers
│   │   ├── repositories/       # Acesso ao banco
│   │   ├── schemas/            # Pydantic
│   │   └── services/           # Lógica de negócio
│   ├── alembic/                # Migrations
│   ├── scripts/seed_db.py      # Seed com 14 salas
│   └── Dockerfile
│
├── frontend/                   # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── pages/              # Login, Dashboard, Rooms, Alerts...
│   │   ├── components/         # Layout, Sidebar, Header...
│   │   ├── services/api.js     # Axios + chamadas à API
│   │   └── store/authStore.js  # Zustand
│   └── Dockerfile
│
├── simulator/                  # Simulador MQTT (I03)
│   └── simulator.py            # 14 salas, temperatura/umidade/presença
│
├── mosquitto/config/           # Configuração do broker MQTT
│
├── Rede/                       # Protótipo HTTP legado (preservado)
│
├── docs/Planejamento/          # Documentação técnica e Kanban
│
└── docker-compose.yml          # Orquestração completa
```

---

## Regras de Negócio Implementadas

| ID | Regra | Status |
|----|-------|--------|
| RN01 | Desligamento automático após 15 min sem presença | ✅ |
| RN02 | Bloqueio do AC com janela aberta > 5 min | ✅ |
| RN03 | Temperatura ideal 23-25°C | ✅ |
| RN04 | Comandos manuais têm prioridade por 30 min | ✅ |
| RN05 | Alerta de consumo diário excessivo (> 50 kWh) | ✅ |
| RN06 | Funcionamento restrito às 07h-21h | ✅ |
| RN07 | Retreinamento diário do modelo ML | ✅ (endpoint /predictions/train) |
| RN08 | Validação de dados antes de persistir | ✅ |
| RN09 | Auditoria completa de todas as ações | ✅ |
| RN10 | Priorizar eficiência energética (setpoint adaptativo) | ✅ |

---

## Equipe

| Dev | Papel | Responsabilidades |
|-----|-------|-------------------|
| **Jhonata** | Backend Lead | FastAPI, DB, JWT, API REST |
| **João Arnaldo** | IoT & MQTT | Broker, Simulador, ESP32 |
| **Rickelmy** | IA & Dados | ML, Pipeline, Regras RN |
| **Felipe Pardinho** | Frontend | React, Dashboard, UI |
| **Claudio Rodrigues** | DevOps & QA | Docker, CI/CD, Testes |

---

## Tópicos MQTT

```
sensors/room/{room_id}/temperature  → { value, tick, timestamp }
sensors/room/{room_id}/humidity     → { value, tick, timestamp }
sensors/room/{room_id}/presence     → { value: 0|1, tick, timestamp }

devices/ac/{device_id}/commands     → { action: "on"|"off"|"setpoint", value }
devices/ac/{device_id}/feedback     → { power: "on"|"off", setpoint, timestamp }
devices/ac/{device_id}/status       → { power, setpoint, temperature, timestamp }

system/alerts/{alert_id}            → { alert_type, severity, message }
```

---

*Documentação gerada em 24/05/2026 — SmartBuilding ExpoTech*
