# Smart Building — Fonte de Dados Completa para Apresentação e Estudo

> **Autor:** Jhonata Soares (Backend Lead)  
> **Projeto:** Smart Building · ExpoTech 2026 · UniFECAF  
> **Uso:** Colar no Google Gemini, anexar junto com `docs/openapi.yaml`, ou ler offline antes da banca.  
> **Repositório:** https://github.com/Jhowsoares/SmartBuilding_ExpoTech  
> **Docs públicas:** https://jhowsoares.github.io/SmartBuilding_ExpoTech/  
> **API base:** `http://localhost:8000/api/v1`  
> **Versão API:** 1.0.0 · OpenAPI 3.1.0  
> **Atualizado:** jun/2026 (alinhado ao código, CI, hardware Sala 302)

---

## Como usar no Gemini

Prompts sugeridos após colar este documento:

1. *"Use este documento como contexto. Sou Jhonata, Backend Lead. Simule perguntas da professora MVP Microsoft sobre REST, OpenAPI e RFC 7807."*
2. *"Explique o fluxo POST /devices/{id}/control até o ventilador ligar na Sala 302."*
3. *"Me teste pasta por pasta do backend, uma pergunta por vez."*
4. *"Compare nossas escolhas de API com boas práticas Microsoft/Azure API Management."*
5. *"Gere flashcards de status codes e onde disparam no código."*

Anexe também: `docs/openapi.yaml` e, se quiser, `revisao_api/Respostas ao Questionário — ExpoTech 2026 (1).docx`.

---

## Índice

1. [Identidade e equipe](#1-identidade-e-equipe)
2. [Monorepo — pasta por pasta](#2-monorepo--pasta-por-pasta)
3. [Arquitetura do sistema](#3-arquitetura-do-sistema)
4. [Backend — anatomia completa (sua parte)](#4-backend--anatomia-completa-sua-parte)
5. [Escolhas de API e justificativas](#5-escolhas-de-api-e-justificativas)
6. [Contrato OpenAPI](#6-contrato-openapi)
7. [Questionário ExpoTech — respostas por critério](#7-questionário-expotech--respostas-por-critério)
8. [Status codes — mapa completo](#8-status-codes--mapa-completo)
9. [Síncrono vs assíncrono](#9-síncrono-vs-assíncrono)
10. [Segurança (OWASP API Top 10)](#10-segurança-owasp-api-top-10)
11. [MQTT e integração IoT](#11-mqtt-e-integração-iot)
12. [Regras de negócio RN01–RN10](#12-regras-de-negócio-rn01rn10)
13. [Sala 302 — hardware real](#13-sala-302--hardware-real)
14. [Fluxos ponta a ponta](#14-fluxos-ponta-a-ponta)
15. [Mapa de estudo para a feira (equipe)](#15-mapa-de-estudo-para-a-feira-equipe)
16. [Roteiro de apresentação (7 min)](#16-roteiro-de-apresentação-7-min)
17. [Demo Swagger (60 segundos)](#17-demo-swagger-60-segundos)
18. [Conceitos extras para a banca](#18-conceitos-extras-para-a-banca)
19. [Perguntas difíceis — respostas prontas](#19-perguntas-difíceis--respostas-prontas)
20. [Glossário](#20-glossário)
21. [Checklist pré-feira](#21-checklist-pré-feira)

---

## 1. Identidade e equipe

### O que é o Smart Building

Sistema de monitoramento e controle inteligente de climatização e energia em edifícios corporativos. Sensores publicam telemetria via MQTT; o backend FastAPI aplica regras de negócio (RN01–RN10), persiste no PostgreSQL e expõe API REST; o dashboard React consome essa API.

**Pitch de 30 segundos:**

> O Smart Building monitora conforto e energia de salas corporativas. Sensores publicam dados via MQTT; o backend FastAPI aplica regras de negócio, persiste no PostgreSQL e expõe uma API REST versionada. O dashboard React consome essa API. Na feira, a Sala 302 usa hardware real: ESP32 + Arduino + ventilador + DHT11 + medição V/A/W.

**Fluxo em uma frase:**

```
Sensor → MQTT → Backend → Regras → PostgreSQL → REST → Dashboard
Comando ← MQTT ← Backend ← POST /devices/{id}/control ← Usuário
```

### Equipe Eng. Computação

| Integrante | Papel | Escopo técnico |
|------------|-------|----------------|
| **Jhonata Soares** | Backend Lead | FastAPI, PostgreSQL, JWT/RBAC, API REST, Docker |
| João Arnaldo | IoT & MQTT | Mosquitto, simulador, ESP32, ngrok |
| Rickelmy | IA & Dados | scikit-learn, RN01–RN10, consumo kWh |
| Felipe Pardinho | Frontend | React 18, Tailwind, Recharts, UX |
| Claudio Rodrigues | DevOps & QA | Docker Compose, Alembic, seed, testes |

### Papel de Jhonata na banca

Dono da **camada central**: API REST versionada, persistência, segurança, integração MQTT↔HTTP, contrato OpenAPI, erros RFC 7807, status codes, arquitetura assíncrona.

---

## 2. Monorepo — pasta por pasta

```
SmartBuilding/
├── backend/           ← SUA CASA (FastAPI, ML, MQTT handlers, testes)
├── frontend/          ← Dashboard React (consome /api/v1)
├── simulator/         ← 13 salas virtuais MQTT (room-302 excluída)
├── firmware/          ← ESP32 gateway BT→MQTT (Sala 302)
├── mosquitto/         ← Config broker MQTT :1883
├── docs/              ← Documentação + openapi.yaml (contrato)
├── revisao_api/       ← Questionário entregue à professora (DOCX)
├── docker-compose.yml ← Orquestra todos os serviços
├── spectral.yml       ← Lint OpenAPI (CI)
├── tools/             ← export_openapi.py, utilitários
└── tests/             ← Testes de contrato API (raiz)
```

| Pasta | O que faz | Você precisa saber |
|-------|-----------|-------------------|
| `backend/` | API, banco, MQTT handlers | **Domínio total** |
| `frontend/` | UI React | Quais endpoints consome |
| `simulator/` | Dados fictícios 13 salas | Não conflita com 302 |
| `firmware/` | Hardware real | Tópicos MQTT `room-302` |
| `docs/openapi.yaml` | Contrato oficial | Design-first + CI |
| `revisao_api/` | Formulário professora | Critérios 1–7 abaixo |

**Decisão — Monorepo:** um `docker compose up` sobe tudo; rastreabilidade; CI único.

---

## 3. Arquitetura do sistema

### Diagrama lógico

```
┌─────────────────────────────────────────────────────────┐
│  BORDA IoT                                              │
│  Simulador (13 salas)  │  ESP32+BT+Arduino (Sala 302)   │
└────────────┬───────────────────────────┬────────────────┘
             │ MQTT :1883                 │
             ▼                            │
      ┌──────────────┐                    │
      │  Mosquitto   │                    │
      └──────┬───────┘                    │
             ▼                            │
┌─────────────────────────────────────────────────────────┐
│  BACKEND FastAPI :8000 /api/v1                          │
│  mqtt/handlers → ml/business_rules → PostgreSQL         │
│  JWT + RBAC + Redis (blacklist, rate limit)             │
│  OpenAPI 3.1 + RFC 7807                                 │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP + Bearer JWT
                           ▼
                ┌─────────────────────┐
                │  React :3000        │
                │  (nginx proxy /api) │
                └─────────────────────┘
```

### Serviços Docker

| Container | Porta | Função |
|-----------|-------|--------|
| sb_postgres | 5432 | PostgreSQL 15 |
| sb_redis | 6379 | Blacklist JWT, rate limit |
| sb_mqtt | 1883 | Mosquitto |
| sb_backend | 8000 | FastAPI + MQTT client |
| sb_frontend | 3000 | React + nginx |
| sb_simulator | — | Simulador Python |
| sb_ngrok | — | Túnel opcional (tablet/feira) |

**Startup backend:** `alembic upgrade head && python -m scripts.seed_db && uvicorn`

### Stack e motivos

| Camada | Tecnologia | Por quê |
|--------|------------|---------|
| API | FastAPI + Pydantic v2 | Async, OpenAPI auto, validação |
| Banco | PostgreSQL + SQLAlchemy 2 + Alembic | ACID, migrations |
| Cache | Redis 7 | Logout real, rate limit |
| IoT | Mosquitto MQTT | Leve para embarcados |
| Auth | JWT HS256 + bcrypt | Stateless + RBAC |
| ML | scikit-learn RandomForest | Predição 24h |
| Frontend | React 18 + Vite + Tailwind | SPA + gráficos |
| Infra | Docker Compose | Demo local/feira |

---

## 4. Backend — anatomia completa (sua parte)

```
backend/
├── app/
│   ├── main.py              ← Bootstrap: lifespan, CORS, erros, routers
│   ├── api/v1/              ← Rotas REST (domínio por arquivo)
│   ├── core/                ← config, JWT, deps (RBAC), exceptions
│   ├── db/                  ← SQLAlchemy async + session
│   ├── models/              ← ORM (tabelas)
│   ├── schemas/             ← Pydantic (validação)
│   ├── repositories/        ← Queries SQL
│   ├── services/            ← Lógica de negócio
│   ├── mqtt/                ← Cliente Paho + handlers IoT
│   ├── ml/                  ← Regras RN + predictor
│   ├── middleware/          ← RateLimitMiddleware
│   └── errors/              ← RFC 7807 handlers
├── alembic/                 ← Migrations
├── scripts/seed_db.py       ← Seed + reconciliação Sala 302
└── tests/                   ← pytest (auth, BOLA, devices, health)
```

### Padrão de camadas

```
HTTP Request
  → api/v1/{domínio}.py     (rota, Depends, status_code)
  → core/deps.py            (JWT, RBAC → 401/403)
  → schemas/                (Pydantic → 422)
  → services/               (regras de aplicação)
  → repositories/           (SQL)
  → models/ + PostgreSQL
```

### Routers (`api/v1/router.py`)

| Arquivo | Prefixo | Auth |
|---------|---------|------|
| health.py | `/health` | Pública |
| auth.py | `/auth` | Pública (login) |
| sensors.py | `/sensors` | Bearer |
| devices.py | `/devices` | Bearer; control = operador+ |
| rooms.py | `/rooms` | Bearer; CRUD = admin |
| alerts.py | `/alerts` | Bearer |
| users.py | `/users` | Admin (exceto `/me`) |
| consumption.py | `/consumption` | Bearer |
| predictions.py | `/predictions` | Bearer; train = admin |

### `main.py` — lifecycle

1. Ping PostgreSQL
2. Inicia MQTT client + subscreve tópicos
3. Registra middleware (CORS, rate limit)
4. Registra handlers RFC 7807
5. Monta `/api/v1/*`

### Modelo de dados (PostgreSQL)

| Tabela | Conteúdo |
|--------|----------|
| users | email, password_hash, role |
| rooms | name, building, floor, area_m2 |
| devices | type, model, serial, mqtt_topic, status, power_on, last_seen_at |
| sensor_data | sensor_id, tipo, valor, tick, timestamp |
| alerts | tipo, severidade, room_id |
| commands | device_id, action, issued_by |
| audit_log | RN09 — auditoria |

**Nota:** "sensor" no MQTT → linhas em `sensor_data`; catálogo físico → tabela `devices`.

### Seed e Sala 302

`scripts/seed_db.py`: 3 usuários, 14 salas, ~48 devices.

**Reconciliação automática** (roda a cada start do backend):

- AC → `"Ventilador (protótipo Arduino)"`
- Tópicos → `devices/ac/room-302/commands`, `sensors/room/room-302/...`
- Remove `presence_sensor` (sem hardware)
- Renomeia sensores → `DHT11 (temperatura/umidade)`

---

## 5. Escolhas de API e justificativas

### REST + `/api/v1`

- Versionamento explícito na URL (Swagger/ReDoc claros)
- v2 convive em paralelo ≥ 6 meses (política depreciação)
- Nível 2 Richardson: substantivos + verbos HTTP (sem `/ligarAC`)

### PATCH vs PUT

- **PATCH** `/rooms/{id}` — altera campos parciais (nome, área)
- **PUT** seria substituição total — não faz sentido no domínio

### POST para controle (não verbo na URL)

```
POST /api/v1/devices/{device_id}/control
{"action": "on"|"off"|"setpoint", "value": 23.0}
```

Ação sobre recurso `device`, não RPC `/ligarAC`.

### Design API-First

1. Contrato discutido antes/durante implementação
2. FastAPI implementa + gera Swagger runtime
3. `tools/export_openapi.py` exporta/enriquece `docs/openapi.yaml`
4. CI `contract-check` bloqueia merge se YAML divergir do código
5. Spectral valida qualidade (`spectral.yml`)

### MQTT separado do REST (IoT)

| Canal | Uso |
|-------|-----|
| MQTT | Telemetria contínua (ESP32, simulador) |
| REST POST /sensors/data | Testes, Swagger, integrações alternativas |
| REST GET /sensors/.../latest | Dashboard (polling) |

**Por quê MQTT:** leve, pub/sub, ideal para ESP32. HTTP contínuo seria pesado.

### Idempotência

| Operação | Idempotente? |
|----------|--------------|
| GET, PATCH, DELETE | Sim |
| POST /sensors/data | Não — cada POST = nova leitura |
| POST /control | Efeito repetido (ligar 2x = ligado) — aceitável MVP |

### Paginação

- `?page=1&size=20` (max 100)
- Offset pagination — adequado ao dashboard (não scroll infinito)
- Resposta: `{ "data": [...], "meta": { page, size, total } }`
- **sort** não exposto no MVP (evitar combinações não testadas)

### HATEOAS parcial

Recursos incluem `links[]` (`self`, `room`, `control`) para descoberta.

### Falha parcial (resiliência)

| Dependência down | Comportamento |
|------------------|---------------|
| PostgreSQL | `GET /health` → **503** RFC 7807 |
| Redis | Health **200 degraded** (blacklist/rate limit degradados) |
| MQTT | API continua; telemetria nova para |

### Depreciação (RFC 8594)

Exemplo: `GET /sensors/{id}/data`

- Depreciação: **2027-01-01**
- Sunset: **2027-06-01**
- Headers: `Deprecation`, `Sunset`
- OpenAPI: `deprecated: true`

Documento: `docs/sistema/deprecation-policy.md`

---

## 6. Contrato OpenAPI

**Arquivo:** `docs/openapi.yaml`  
**Versão:** OpenAPI 3.1.0 · API 1.0.0  
**Superfície:** 26 paths · 36 operações

### Interfaces

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/api/docs |
| ReDoc local | http://localhost:8000/api/redoc |
| ReDoc público | https://jhowsoares.github.io/SmartBuilding_ExpoTech/api.html |
| OpenAPI JSON | http://localhost:8000/api/openapi.json |

### Paths completos

```
GET     /api/v1/health
POST    /api/v1/auth/login
POST    /api/v1/auth/refresh
POST    /api/v1/auth/logout
POST    /api/v1/sensors/data
GET     /api/v1/sensors
GET     /api/v1/sensors/{sensor_id}
GET     /api/v1/sensors/{sensor_id}/data      ← deprecated
GET     /api/v1/sensors/{sensor_id}/latest
GET|POST /api/v1/devices
GET|PATCH|DELETE /api/v1/devices/{device_id}
POST    /api/v1/devices/{device_id}/control
GET|POST /api/v1/rooms
GET|PATCH|DELETE /api/v1/rooms/{room_id}
GET|POST /api/v1/alerts
GET     /api/v1/alerts/history
GET     /api/v1/alerts/{alert_id}
POST    /api/v1/alerts/{alert_id}/acknowledge
POST    /api/v1/alerts/{alert_id}/resolve
GET|POST /api/v1/users
GET     /api/v1/users/me
GET|PATCH|DELETE /api/v1/users/{user_id}
GET     /api/v1/consumption
GET     /api/v1/consumption/summary
GET     /api/v1/predictions/24h
POST    /api/v1/predictions/train
```

### Schema ProblemDetail (RFC 7807)

```json
{
  "type": "https://smartbuilding.local/errors/unauthorized",
  "title": "Não autenticado",
  "status": 401,
  "detail": "Token ausente ou inválido.",
  "instance": "/api/v1/rooms",
  "errors": [],
  "rule": "RN04"
}
```

Campos opcionais: `errors[]` (422), `rule` (409), `subsystems` (503 health).

### Security

- `HTTPBearer` — JWT access token
- Login: `POST /auth/login` → `access_token` + `refresh_token`

### Governança Spectral (`spectral.yml`)

Regras CI (error): operationId, summary, 4xx com ProblemDetail  
Regras warn: snake_case, kebab-case paths, tags, `/api/v1/` obrigatório

### Credenciais demo

| Email | Senha | Papel |
|-------|-------|-------|
| admin@smartbuilding.local | admin123 | admin |
| operador@smartbuilding.local | op123 | operador |
| visualizador@smartbuilding.local | view123 | visualizador |

---

## 7. Questionário ExpoTech — respostas por critério

> Fonte: `revisao_api/Respostas ao Questionário — ExpoTech 2026 (1).docx`  
> Pesos indicados no formulário da professora.

### Critério 1 — Arquitetura da API & Protocolos (20%)

**Métodos HTTP:** PATCH para atualização parcial; POST `/control` para ações; sem RPC na URL.

**Status codes:** ver [seção 8](#8-status-codes--mapa-completo).

**Modelagem:** substantivos REST versionados; rotas removidas que não tinham implementação (`/reports/*`, `/rooms/{id}/commands`).

**Versionamento:** `/api/v1/` na URL — explícito no Swagger.

**OpenAPI:** design-first → export contínuo → contract-check no CI.

**Falha parcial:** health 503 se DB down; MQTT down não derruba API.

**Evidências:** `rooms.py`, `devices.py`, `openapi.yaml`, `ci.yml`, `health.py`.

### Critério 2 — DX & Documentação (20%)

**TTFC (Time To First Call):** Swagger → login → Authorize → GET /rooms.

**Endpoint crítico:** `POST /sensors/data` (201); produção usa MQTT.

**Erros RFC 7807:** todos 4xx/5xx documentados no OpenAPI.

**Paginação:** page/size, max 100.

**Spectral:** lint no CI.

**Evidências:** `handlers.py`, `export_openapi.py`, ReDoc GitHub Pages.

### Critério 3 — Segurança (15%)

**BOLA (API1):** RBAC + `/users/me`; rotas admin-only; testes `test_bola.py`.

**JWT (API2):** access 60 min, refresh 7 dias, blacklist Redis no logout.

**Validação (API4):** Pydantic antes da lógica → 422.

**Rate limit (API4):** middleware + SlowAPI → 429 + Retry-After.

**BOPLA (API3):** `password_hash` nunca na resposta; role só via admin.

**Cache LGPD:** `Cache-Control: private, no-store` em `/api/*`.

**Evidências:** `deps.py`, `auth.py`, `middleware/rate_limit.py`, `schemas/user.py`.

### Critério 4 — Performance & Resiliência (10%)

**Paginação:** teto size=100.

**Rate limit:** protege contra loop/retry.

**ML train:** Semaphore(1) + 503 se treino em andamento.

**Idempotência:** PATCH idempotente; POST sensor nova leitura.

**Evidências:** `predictions.py`, `rate_limit.py`.

### Critério 5 — Ciclo de Vida & Governança (10%)

**CI jobs:** lint-openapi, test-backend (pytest + Postgres nativo), contract-check.

**Depreciação:** policy doc + headers + testes `test_deprecation.py`.

**Planos futuros:** APM/Prometheus, API Gateway, Pact (não MVP).

**Evidências:** `.github/workflows/ci.yml`, `deprecation-policy.md`.

### Critério 6 — Integração Multidisciplinar (10%)

| Área | Interface com API |
|------|-------------------|
| Computação | FastAPI, Docker, CI |
| Redes/IoT | MQTT, ESP32, simulador |
| IA | `/predictions`, RN01–RN10 |
| Elétrica | Telemetria V/A/W, controle ventilador |
| Civil/Produção | Salas cadastradas, `/consumption` kWh/R$ |

### Critério 7 — Protótipo & Repositório (15%)

**POC:** `docker compose up` → health 200, Swagger, simulador, Sala 302 real.

**Testes:** `backend/tests/` no CI.

**GitHub Pages:** documentação integrada.

---

## 8. Status codes — mapa completo

### Onde vivem

Status codes existem **somente na camada HTTP REST** (`/api/v1/*`). MQTT/ESP32 não usam HTTP status.

Formato de erro: **RFC 7807** (`application/problem+json`).

Handlers: `backend/app/errors/handlers.py` + `backend/app/core/exceptions.py`

### 2xx — Sucesso

| Code | Onde | Exemplos |
|------|------|----------|
| **200** | GET/PATCH/POST com corpo | `/rooms`, `/control`, `/auth/login` |
| **201** | POST criação | `/rooms`, `/devices`, `/sensors/data` |
| **202** | Aceito async | `POST /predictions/train` |
| **204** | DELETE sem corpo | `/rooms/{id}`, `/devices/{id}`, `/users/{id}` |

### 4xx — Erro do cliente

| Code | Onde dispara | Exemplo |
|------|--------------|---------|
| **400** | HTTPException genérico | Raro |
| **401** | `UnauthorizedError`, `deps.py`, `auth.py` | Sem token, credencial errada, token revogado |
| **403** | `ForbiddenError`, RBAC | Visualizador tenta POST /devices |
| **404** | `ResourceNotFoundError` | Sala/device/sensor inexistente |
| **405** | Starlette automático | Verbo HTTP errado |
| **409** | `ConflictError` | E-mail duplicado POST /users |
| **422** | Pydantic + `BusinessRuleError` | Campo inválido; setpoint fora 16–30°C |
| **429** | RateLimitMiddleware + SlowAPI | Login >10/min |

### 5xx — Erro do servidor

| Code | Onde | Exemplo |
|------|------|---------|
| **500** | Exception não tratada | Bug interno |
| **503** | `health.py`, `predictions.py` | DB offline; treino ML ocupado |

### Fluxo visual

```
Request → RateLimit (429) → JWT (401) → RBAC (403) → Pydantic (422)
       → Service (404, 409, 422) → Success (200/201/202/204)
       → Unhandled (500) | Health DB down (503)
```

### 401 vs 403 vs 422 vs 409

| Code | Pergunta que responde |
|------|----------------------|
| 401 | Quem é você? (identidade) |
| 403 | Sei quem é, mas não pode (papel) |
| 422 | JSON ok, valor/regra inválida |
| 409 | JSON ok, conflito de estado (e-mail existe) |

---

## 9. Síncrono vs assíncrono

| Camada | Modelo |
|--------|--------|
| API REST (FastAPI) | **Assíncrona** — async def, AsyncSession, asyncpg |
| MQTT handlers | **Event-driven** — thread Paho → run_coroutine_threadsafe |
| Frontend | **HTTP async** (axios) + polling 5s (não WebSocket) |
| ESP32/Arduino | **Loop síncrono** + FreeRTOS tasks |
| Simulador | **Loop síncrono** a cada 5s |

**Resposta para banca:** sistema **híbrido** — REST async para usuários; MQTT pub/sub para IoT; firmware síncrono na borda.

---

## 10. Segurança (OWASP API Top 10)

| Risco | Mitigação no projeto |
|-------|---------------------|
| API1 BOLA | RBAC + `/users/me` + testes |
| API2 Auth | JWT + refresh + blacklist logout |
| API3 BOPLA | Schemas separados Create/Response |
| API4 Unrestricted | Rate limit + validação Pydantic |
| Rate limit | Redis sliding window |

### RBAC

| Papel | Permissões |
|-------|------------|
| admin | Tudo |
| operador | Controlar devices, ler dados |
| visualizador | Somente leitura |

Implementação: `require_admin`, `require_operador`, `require_visualizador` em `core/deps.py`.

### Rate limits

| Rota | Limite |
|------|--------|
| POST /auth/login | 10/min |
| POST /sensors/data | 120/min |
| POST /predictions/train | 3/5min |
| /api/v1/* default | 60/min |

---

## 11. MQTT e integração IoT

### Telemetria (publish → backend)

```
sensors/room/{slug}/temperature
sensors/room/{slug}/humidity
sensors/room/{slug}/presence
sensors/room/{slug}/window
sensors/room/{slug}/power
sensors/room/{slug}/voltage
sensors/room/{slug}/current
```

Payload: `{"value": 24.3, "tick": 42, "timestamp": "..."}`

### Comandos (backend → hardware)

```
devices/ac/{slug}/commands
{"action": "on"|"off"|"setpoint", "value": 23.0}
```

Publica em **dois tópicos**: UUID do device + slug da sala (`room-302`).

### Feedback

```
devices/ac/{slug}/feedback
{"power": "on"|"off", "setpoint": 24.0}
```

→ Atualiza `devices.power_on`, `status=online`, `last_seen_at`.

### Handler (`mqtt/handlers.py`)

1. Parse topic + payload
2. INSERT `sensor_data`
3. Marca devices ONLINE
4. `BusinessRulesEngine.evaluate()`
5. Executa ações (MQTT power_off, alertas, audit)

### Simulador vs real

- Simulador: 13 salas, padrões realistas (seno diário, presença por horário)
- `EXCLUDE_ROOMS=room-302` — hardware exclusivo ESP32

---

## 12. Regras de negócio RN01–RN10

Arquivo: `backend/app/ml/business_rules.py`  
Ordem: **RN08 → RN06 → RN04 → RN01/RN02/RN03/RN05/RN10**

| ID | Regra | Parâmetro |
|----|-------|-----------|
| RN01 | Desligar AC sem presença | 15 min |
| RN02 | Bloquear AC janela aberta | 5 min |
| RN03 | Setpoint ideal | 23–25°C |
| RN04 | Override manual pós-controle dashboard | 30 min |
| RN05 | Alerta consumo alto | > 50 kWh/dia |
| RN06 | Horário comercial | 07h–21h |
| RN07 | Retreinar ML | POST /predictions/train |
| RN08 | Validar leitura | Temp 5–55°C |
| RN09 | Auditoria | audit_log |
| RN10 | Eficiência energética | kWh por desvio térmico |

Avaliadas **a cada mensagem MQTT**, não a cada HTTP request.

---

## 13. Sala 302 — hardware real

| Componente | Origem | Tópico MQTT |
|------------|--------|-------------|
| Temperatura | DHT11 ESP32 GPIO4 | `.../temperature` |
| Umidade | DHT11 ESP32 | `.../humidity` |
| Tensão/Corrente/Potência | Arduino via BT | `.../voltage`, `/current`, `/power` |
| Ventilador | Arduino via BT | `devices/ac/room-302/commands` |

**Calibração:** `VOLTAGE_CALIBRATION ≈ 3.74` (127V / ~34V bruto).

**Devices no banco (pós-reconciliação):**

1. Ventilador (protótipo Arduino)
2. DHT11 (temperatura)
3. DHT11 (umidade)

**Frontend:** card "Clima & Energia" — polling 5s em `sensor-*-room-302/latest`.

---

## 14. Fluxos ponta a ponta

### Telemetria

```
DHT11/Arduino → ESP32 → MQTT → handlers.py → sensor_data
  → GET /sensors/sensor-temperature-room-302/latest → React
```

### Comando

```
React "Ligar" → POST /devices/{id}/control + JWT
  → device_service → MQTT room-302 → ESP32 → BT → Arduino
  → feedback MQTT → UPDATE power_on → dashboard
```

---

## 15. Mapa de estudo para a feira (equipe)

### Guardiões na banca

| Tema | Dono | Backup |
|------|------|--------|
| API / REST / OpenAPI | **Jhonata** | Claudio |
| MQTT / Hardware | João | Elétrica |
| Regras / Consumo / ML | Rickelmy | Jhonata |
| Dashboard | Felipe | Jhonata |
| DevOps / Docker | Claudio | Jhonata |

### O que NÃO gastar tempo

- Pinagem GPIO (só se elétrica perguntar)
- Calibração fina ZMPT101B
- Todos os 30+ endpoints — citar categorias
- Histórico de bugs (MQTT -2, D14 vs D4)

### Outras engenharias — frases de 30s

**Civil:** Maquete ↔ cadastro de salas (302 = laboratório).

**Produção:** `/consumption` → kWh e custo R$ para ROI.

**Elétrica:** ZMPT101B + ACS712 + DHT11; ESP32 ponte BT→MQTT.

---

## 16. Roteiro de apresentação (7 min)

| Tempo | Quem | Conteúdo |
|------:|------|----------|
| 0:30 | Integrador | Pitch problema/solução |
| 1:00 | **Jhonata** | Diagrama 3 camadas + monorepo |
| 2:00 | João + Felipe | Demo Sala 302 ao vivo |
| 1:00 | Rickelmy | RN01–RN05 + consumo kWh |
| 1:00 | **Jhonata** | API OpenAPI, JWT, RFC 7807, status codes |
| 0:30 | Civil / Produção / Elétrica | Integração |
| 0:30 | Encerramento | Docker local, GitHub Pages |

---

## 17. Demo Swagger (60 segundos)

1. `POST /auth/login` → copiar `access_token`
2. **Authorize** Bearer
3. `GET /health`
4. `GET /rooms` → Sala 302
5. `GET /sensors/sensor-temperature-room-302/latest`
6. `POST /devices/{id}/control` → `{"action":"on"}`
7. (Opcional) `GET /consumption?period=24h`

---

## 18. Conceitos extras para a banca

### Maturidade REST (Richardson)

| Nível | O que é | Nós |
|-------|---------|-----|
| 0 | Um endpoint RPC | ❌ evitamos `/ligarAC` |
| 1 | Recursos + HTTP | ✅ `/rooms`, `/devices` |
| 2 | Verbos HTTP corretos | ✅ GET/POST/PATCH/DELETE |
| 3 | HATEOAS | Parcial (`links[]`) |

### JWT vs Session

Escolhemos **JWT stateless** + Redis só para blacklist (logout). Escala horizontal sem sticky session.

### Pub/Sub vs Request/Response

- **MQTT pub/sub:** telemetria assíncrona, many-to-one
- **REST request/response:** comandos do usuário, consultas do dashboard

### Problem Details (RFC 7807) vs erro genérico

Cliente trata `status`, `title`, `detail` de forma uniforme — padrão Microsoft/IETF adotado em APIs enterprise.

### Deprecation (RFC 8594)

Headers `Deprecation` e `Sunset` avisam clientes antes de breaking change — governança de API madura.

### API Gateway (plano futuro)

Kong/Azure APIM na frente: TLS, rate limit global, auth — backend foca regras de negócio.

### BFF (Backend for Frontend)

No MVP, React consome API diretamente via nginx proxy. BFF dedicado seria evolução se mobile/native multiplicar.

### Circuit Breaker

Não implementado completo; usamos **degradação controlada** (503 health, semáforo ML train).

### Idempotency-Key (plano)

Header `Idempotency-Key` em POST /sensors/data — evolução futura com constraint `sensor_id + tick`.

### CQRS leve

- **Write path IoT:** MQTT → handlers
- **Read path UI:** REST GET /latest, /data
- Mesmo banco PostgreSQL (não CQRS estrito)

### Async I/O (Python)

FastAPI + asyncpg: thread não bloqueia esperando DB — atende muitas requisições concorrentes no mesmo processo.

### Design-first vs Code-first

Começamos design-first (contrato); operação atual exporta código → YAML (governança contínua via CI).

### LGPD

`Cache-Control: no-store` — dados de consumo/usuário não cacheados em proxy/browser.

### Contrato vs implementação

Três camadas de garantia: Pydantic runtime, OpenAPI versionado, Spectral + contract-check CI.

---

## 19. Perguntas difíceis — respostas prontas

| Pergunta | Resposta |
|----------|----------|
| Por que FastAPI? | Async, OpenAPI auto, Pydantic, ideal I/O DB+Redis |
| Por que MQTT e não HTTP no sensor? | Leve, pub/sub, padrão IoT, ESP32 |
| API síncrona ou assíncrona? | Híbrida: REST async, MQTT event-driven |
| Contrato bate com código? | export_openapi.py + contract-check CI |
| 401 vs 403? | Identidade vs permissão |
| 422 vs 409? | Validação/regra vs conflito de estado |
| O que se MQTT cair? | API continua; telemetria para |
| O que se PostgreSQL cair? | Health 503; API não persiste |
| Por que PATCH e não PUT? | Atualização parcial de sala |
| Por que POST /control? | Ação sobre recurso, não verbo na URL |
| Como prova BOLA? | test_bola.py + RBAC + /users/me |
| Logout invalida token? | Sim, blacklist Redis |
| ML substitui regras? | Não — ML prediz; regras automatizam |
| Diferença simulador vs 302? | Simulador 13 salas; 302 hardware real excluído |

---

## 20. Glossário

| Termo | Significado |
|-------|-------------|
| slug | ID textual da sala: `room-302` |
| RFC 7807 | Problem Details for HTTP APIs |
| RFC 8594 | HTTP Deprecation/Sunset headers |
| BOLA | Broken Object Level Authorization |
| BOPLA | Broken Object Property Level Authorization |
| RBAC | Role-Based Access Control |
| TTFC | Time To First Call (primeira chamada API ok) |
| pub/sub | Publish/Subscribe MQTT |
| seed | População inicial do banco |
| reconciliação | Ajuste automático devices Sala 302 |
| asyncpg | Driver PostgreSQL assíncrono |
| Spectral | Linter OpenAPI |
| contract-check | CI compara YAML exportado vs versionado |

---

## 21. Checklist pré-feira

### Ambiente

- [ ] `docker compose up -d` rodando
- [ ] `GET /health` → 200
- [ ] ESP32 conectado (Sala 302)
- [ ] Swagger aberto em aba separada
- [ ] Dashboard Sala 302 com "Clima & Energia" ao vivo

### Jhonata — dominar

- [ ] Explicar monorepo pasta por pasta
- [ ] Desenhar diagrama 3 camadas no quadro
- [ ] Demo Swagger 60s de memória
- [ ] 401 vs 403 vs 422 vs 409
- [ ] Fluxo POST /control → MQTT → ventilador
- [ ] Critérios 1–3 do questionário (20%+20%+15%)
- [ ] Onde está `openapi.yaml` e o que o CI valida

### Plano B

> "Simulador cobre 13 salas; 302 depende do gateway. Mostramos fluxo completo no Swagger e histórico já persistido."

---

## Frase de encerramento (Jhonata)

> Implementamos uma API REST versionada, documentada em OpenAPI 3.1, com autenticação JWT, RBAC, erros RFC 7807 e rate limiting. O backend assíncrono integra telemetria MQTT, regras RN01–RN10 e PostgreSQL — com hardware real validando o fluxo na Sala 302. O contrato é governado por Spectral e contract-check no CI, alinhado ao questionário ExpoTech entregue à professora.

---

## Referências rápidas de arquivos

| Tema | Arquivo |
|------|---------|
| Entrada API | `backend/app/main.py` |
| Rotas | `backend/app/api/v1/*.py` |
| JWT/RBAC | `backend/app/core/deps.py`, `security.py` |
| Erros | `backend/app/errors/handlers.py`, `core/exceptions.py` |
| MQTT | `backend/app/mqtt/handlers.py`, `client.py` |
| Regras | `backend/app/ml/business_rules.py` |
| Controle device | `backend/app/services/device_service.py` |
| Contrato | `docs/openapi.yaml` |
| Lint contrato | `spectral.yml` |
| CI | `.github/workflows/ci.yml` |
| Export OpenAPI | `tools/export_openapi.py` |
| Depreciação | `docs/sistema/deprecation-policy.md` |
| Questionário | `revisao_api/Respostas ao Questionário — ExpoTech 2026 (1).docx` |
| Seed + 302 | `backend/scripts/seed_db.py` |
| Testes BOLA | `backend/tests/test_bola.py` |

---

*Documento gerado para estudo e apresentação — Smart Building ExpoTech 2026.*
