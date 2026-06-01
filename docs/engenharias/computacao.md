# Engenharia da Computação

A Engenharia da Computação desenvolve a **plataforma digital** do Smart Building: API REST, ingestão MQTT, machine learning, dashboard e infraestrutura Docker.

> Esta página é um **resumo integrador**. A documentação técnica completa está em [`docs/sistema/`](../sistema/architecture.md).

---

## O que entregamos

| Camada | Tecnologia | Documentação |
|--------|------------|--------------|
| API REST | FastAPI, OpenAPI 3.1, JWT/RBAC | [api.md](../sistema/api.md) |
| Banco | PostgreSQL 15, SQLAlchemy, Alembic | [architecture.md](../sistema/architecture.md) |
| Cache / tokens | Redis 7 | [architecture.md](../sistema/architecture.md) |
| IoT | Mosquitto MQTT, simulador Python, ESP32 | [mqtt.md](../sistema/mqtt.md) |
| ML | scikit-learn (RandomForest) | [business-rules.md](../sistema/business-rules.md) |
| Frontend | React 18, Tailwind, Recharts | GitHub Pages [index.html](../index.html) |
| DevOps | Docker Compose (6 serviços) | [setup.md](../guias/setup.md) |

---

## Fluxo de dados (Computação no centro)

```
Simulador / ESP32 / Arduino+BT
         ↓ MQTT
    Backend FastAPI
    ├── Persiste sensor_data (PostgreSQL)
    ├── Aplica regras RN01–RN10
    ├── Gera alertas e consumo
    └── Expõe REST /api/v1/*
         ↓ HTTP
    Dashboard React (localhost:3000)
```

---

## Destaques para avaliação

- **30+ endpoints** REST versionados em `/api/v1/`
- **10 regras de negócio** documentadas (RN01–RN10)
- **Predição 24h** de consumo com fallback gracioso
- **Testes automatizados** (`backend/tests/`)
- **Swagger UI** e contrato `openapi.yaml` (design-first)

---

## Como rodar

```bash
git clone https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git
cd SmartBuilding_ExpoTech
docker compose up --build
```

| Serviço | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Swagger | http://localhost:8000/api/docs |
| GitHub Pages | https://jhowsoares.github.io/SmartBuilding_ExpoTech/ |

Login: `admin@smartbuilding.local` / `admin123`

---

## Integração com outras engenharias

| Área | Interface com Computação |
|------|-------------------------|
| **Elétrica** | MQTT / Bluetooth bridge → tópicos de telemetria |
| **Civil** | Cadastro de salas reflete layout real/maquete |
| **Produção** | Endpoint `/consumption` gera kWh e custo em R$ |

---

## Equipe (Eng. Computação)

Ver detalhes em [team.md](../sistema/team.md):

Jhonata Soares · João Arnaldo · Rickelmy · Felipe Pardinho · Claudio Rodrigues

---

## Documentação técnica completa

- [Índice geral](../README.md)
- [Arquitetura](../sistema/architecture.md)
- [Setup](../guias/setup.md)

## PDFs oficiais (Computação)

- [Arquitetura do sistema (PDF)](entregaveis/em_pdf/Arquitetura%20do%20sistema.pdf)
- [Escopo e arquitetura funcional (PDF)](entregaveis/em_pdf/Relatorio_de_Escopo_e_Arquitetura_Funcional.pdf)
