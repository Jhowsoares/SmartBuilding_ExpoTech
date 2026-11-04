# 🏛️ Arquitetura e Fluxo de Dados

## 📌 Visão Geral

O ecossistema **Smart Building** foi projetado para monitoramento e automação predial em tempo real, com foco em eficiência energética. A arquitetura desacopla a camada de borda (IoT), o broker de mensageria, o backend assíncrono e o painel de controle front-end.

**Exemplo de Caso de Uso (Automação Baseada em Regras):**
> *Ocupante ausente por 15 minutos em uma sala corporativa:*
> 1. Sensor de presença detecta ausência $\rightarrow$ Publica evento via MQTT.
> 2. Motor de Regras (`RN01`) é acionado no backend.
> 3. Sistema envia comando de desligamento do Ar-Condicionado (`AC`) de forma assíncrona.
> 4. Auditoria registra o evento $\rightarrow$ O Dashboard React atualiza em tempo real.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Justificativa Técnica |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts | SPA reativa, alta performance de build e renderização de gráficos em tempo real. |
| **Backend** | FastAPI (Python), Pydantic v2 | Execução assíncrona (`async/await`), documentação automática OpenAPI e tipagem robusta. |
| **Banco de Dados** | PostgreSQL 15, SQLAlchemy 2, Alembic | Integridade relacional (ACID), suporte a migrações e consultas eficientes. |
| **Cache & Sockets** | Redis 7 | Gerenciamento de Blacklist para tokens JWT (logout seguro) e cache de leituras. |
| **Mensageria IoT** | Eclipse Mosquitto MQTT | Protocolo leve, ideal para comunicação de baixa largura de banda com microcontroladores. |
| **Machine Learning** | scikit-learn (Random Forest) | Modelo preditivo para projeção de consumo energético nas próximas 24h. |
| **Segurança** | JWT, bcrypt, RBAC | Controle de acesso baseado em papéis (3 níveis) com revogação via Redis. |
| **Infraestrutura** | Docker Compose | Orquestração de containers para subida instantânea de todo o ambiente de desenvolvimento. |

---

## 📐 Diagrama de Arquitetura

```text
 ╔══════════════════════════════════════════════════════════════════════╗
 ║                        BORDAS / DISPOSITIVOS IOT                     ║
 ║  ESP32 + Sensores (Físico)        Simulador Docker (14 Salas)        ║
 ╚═══════════════════╪══════════════════════════════════╪═══════════════════╝
                     │ (MQTT Publish)                     │ (MQTT Publish)
                     ▼                                    ▼
 ╔══════════════════════════════════════════════════════════════════════╗
 ║                     MOSQUITTO BROKER (Porta 1883)                    ║
 ╚═══════════════════════╦══════════════════════════════════════════════╝
                         │ (MQTT Subscribe / Wildcard)
                         ▼
 ╔══════════════════════════════════════════════════════════════════════╗
 ║                    FASTAPI BACKEND (Porta 8000)                      ║
 ║  MQTT Handler ──> Motor de Regras (RN01-10) ──> SQLAlchemy ──> Postgres║
 ║                                               Redis (JWT Blacklist)  ║
 ╚═══════════════════════════════════════╦══════════════════════════════╝
                                         │ REST API / JWT
                                         ▼
 ╔══════════════════════════════════════════════════════════════════════╗
 ║                    REACT FRONTEND (Porta 3000)                       ║
 ╚══════════════════════════════════════════════════════════════════════╝

```

*Consulte a especificação interativa na [Landing Page da Documentação](https://jhowsoares.github.io/SmartBuilding_ExpoTech/).*

---

## 🔄 Caminho do Dado (Exemplo: Leitura de Temperatura)

1. **Captação:** O microcontrolador publica no tópico MQTT `sensors/room/room-101/temperature` com um payload JSON (`{"value": 24.3, ...}`).
2. **Mensageria:** O broker Mosquitto intercepta e repassa a mensagem ao subscriber do backend usando filtros por wildcard (`sensors/room/+/temperature`).
3. **Ingestão Assíncrona:** O `MQTT Handler` faz a ponte thread-safe (`asyncio`) para persistência com o driver assíncrono do banco (`asyncpg`).
4. **Processamento:** O `Business Rules Engine` avalia o contexto da regra contra a nova leitura.
5. **Persistência:** Os dados consolidados são salvos nas tabelas de telemetria, comandos ou alertas do PostgreSQL.
6. **Consumo:** A REST API serve os dados filtrados via endpoint `/api/v1/sensors/{id}/data`.
7. **Renderização:** O front-end consome via polling os dados e atualiza o painel visual.

---

## 💡 Decisões de Arquitetura (Design Decisions)

### 1. Por que utilizar o Redis?

* **Blacklist de JWT (Logout Efetivo):** Permite invalidar tokens antes do tempo de expiração nativo, algo que o JWT stateless tradicional não suporta de forma isolada.
* **Cache de Leituras Frequentes:** Reduz a carga de I/O em cima do banco relacional principal.

### 2. Por que arquitetura em Monorepositório?

* **Coesão na IDE:** Facilita o mapeamento cruzado de contratos entre os modelos do Pydantic (Backend) e as interfaces (Frontend).
* **Developer Experience (DX):** O comando `docker compose up` levanta o stack completo instantaneamente para qualquer avaliador ou novo desenvolvedor.

