<div align="center">

# 🏢 Smart Building
### Sistema de Controle Inteligente de Ar-Condicionado

**ExpoTech 2026 · Engenharia da Computação**

[![API Docs](https://img.shields.io/badge/API-Swagger_UI-85ea2d?logo=swagger)](http://localhost:8000/api/docs)
[![ReDoc](https://img.shields.io/badge/Docs-ReDoc_GitHub_Pages-orange?logo=readme)](https://jhowsoares.github.io/SmartBuilding_ExpoTech/)
[![Docker](https://img.shields.io/badge/Deploy-Docker_Compose-2496ed?logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_3.11-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61dafb?logo=react)](https://react.dev/)
[![MQTT](https://img.shields.io/badge/IoT-MQTT_Mosquitto-660066?logo=eclipse-mosquitto)](https://mosquitto.org/)

> *"Economize energia, respeite o conforto, automatize com inteligência."*

</div>

---

## 📋 Sumário

| # | Seção |
|---|-------|
| 1 | [Visão Geral do Ecossistema](#-visão-geral-do-ecossistema) |
| 2 | [Arquitetura e Fluxo End-to-End](#-arquitetura-e-fluxo-end-to-end) |
| 3 | [Guia de Hardware de Bancada (ESP32)](#-guia-de-hardware-de-bancada) |
| 4 | [Estratégia de Rede para a ExpoTech](#-estratégia-de-rede-para-a-expotech) |
| 5 | [Setup Local em 3 Passos](#-setup-local-em-3-passos) |
| 6 | [Credenciais de Acesso](#-credenciais-de-acesso) |
| 7 | [Contrato da API e Documentação Ativa](#-contrato-da-api-e-documentação-ativa) |
| 8 | [Testando a API — Guia Completo](#-testando-a-api) |
| 9 | [Regras de Negócio e Mapeamento de Código](#-regras-de-negócio) |
| 10 | [Estrutura do Projeto](#-estrutura-do-projeto) |
| 11 | [Tópicos MQTT — Protocolo dos Sensores](#-tópicos-mqtt) |
| 12 | [Variáveis de Ambiente](#-variáveis-de-ambiente) |
| 13 | [Equipe e Papéis Técnicos](#-equipe) |

---

## 🏢 Visão Geral do Ecossistema

O **Smart Building** é um sistema IoT completo para **monitoramento e controle inteligente de climatização** em edifícios corporativos. Em vez de um simples termostato, o sistema raciocina sobre presença humana, temperatura ambiente, janelas abertas e histórico de consumo para **tomar decisões automatizadas** — desligando ACs em salas vazias, ajustando setpoints para a faixa de conforto ideal e gerando alertas de eficiência energética.

### O que o sistema faz, na prática

```
Alguém sai da sala por 15 minutos?
  → O sensor de presença detecta ausência
  → A regra RN01 é ativada
  → O AC é desligado automaticamente via MQTT
  → A ação é registrada na tabela de auditoria
  → O dashboard atualiza em tempo real
```

### Stack Tecnológico

| Camada | Tecnologia | Por que escolhemos |
|--------|------------|--------------------|
| Frontend | React 18 + Vite + TailwindCSS + Recharts | SPA reativa, build rápido, gráficos em tempo real |
| Backend | FastAPI (Python 3.11) + Pydantic v2 | Async nativo, documentação automática, validação rigorosa |
| Banco de dados | PostgreSQL 15 + SQLAlchemy 2.0 + Alembic | ACID, histórico imutável, migrations versionadas |
| Cache / Blacklist JWT | Redis 7 | Sub-milissegundo para tokens revogados e leituras quentes |
| Mensageria IoT | Mosquitto 2 (MQTT v3.1.1) | Protocolo leve ideal para dispositivos embarcados |
| Inteligência Artificial | scikit-learn (RandomForest + LinearRegression) | Predição de consumo 24h com retreinamento sob demanda |
| Autenticação | JWT + bcrypt + blacklist Redis | RBAC com 3 papéis, logout real com revogação de token |
| Infraestrutura | Docker Compose | Um comando sobe tudo — sem instalação local |

---

## 📐 Arquitetura e Fluxo End-to-End

### Diagrama do Sistema

```
╔══════════════════════════════════════════════════════════════════════╗
║                        HARDWARE / BORDA IoT                          ║
║                                                                      ║
║  ┌─────────────────┐    ┌──────────────────────────────────────────┐ ║
║  │ ESP32 + BME280  │    │          Simulador Docker                │ ║
║  │ (Temp/Umidade)  │    │  14 salas × 5s → temperatura, umidade,  │ ║
║  │ ESP32 + HC-SR501│    │  presença publicados em paralelo         │ ║
║  │ (Presença PIR)  │    └──────────────────────────────────────────┘ ║
║  └────────┬────────┘                          │                      ║
╚═══════════╪══════════════════════════════════╪══════════════════════╝
            │  MQTT publish                    │  MQTT publish
            ▼                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                   MOSQUITTO BROKER  :1883                             ║
║              (broker MQTT open-source, protocolo leve)                ║
╚═══════════════════════╦═══════════════════════════════════════════════╝
                        │  MQTT subscribe (paho-mqtt)
                        ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                    FASTAPI BACKEND  :8000                             ║
║                                                                       ║
║  ┌───────────────┐  ┌──────────────────┐  ┌────────────────────────┐ ║
║  │  MQTT Handler │→ │ BusinessRules    │→ │  Pydantic v2           │ ║
║  │  (thread-safe │  │ Engine RN01-RN10 │  │  (validação rigorosa)  │ ║
║  │  async bridge)│  │  scikit-learn ML │  │                        │ ║
║  └───────────────┘  └──────────────────┘  └──────────┬─────────────┘ ║
║                                                       │               ║
║  ┌────────────────────────────────────────────────────▼─────────────┐ ║
║  │                    SQLAlchemy 2.0 (async)                         │ ║
║  └──────────────────────┬──────────────────────────────────────────┘ ║
║                         │                                             ║
║  ┌──────────────────────▼────┐   ┌──────────────────────────────────┐ ║
║  │  PostgreSQL :5432          │   │  Redis :6379                     │ ║
║  │  ├── sensor_data           │   │  ├── blacklist:token[...] (JWT)  │ ║
║  │  ├── devices               │   │  └── cache de leituras recentes  │ ║
║  │  ├── rooms                 │   └──────────────────────────────────┘ ║
║  │  ├── alerts                │                                        ║
║  │  ├── commands (auditoria)  │                                        ║
║  │  └── audit_logs            │                                        ║
║  └───────────────────────────┘                                        ║
║                                                                       ║
║  REST API /api/v1  ←──────────────────────────────────────────────── ║
╚═══════════════════════════════════════╦═══════════════════════════════╝
                                        │  HTTP + JWT
                                        ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                    REACT FRONTEND  :3000                              ║
║                                                                       ║
║  Dashboard  │  Salas + Controle AC  │  Alertas  │  Relatórios        ║
║  Predições  │  Status do Sistema    │  Usuários │  Histórico         ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 🔍 O Caminho do Dado — Temperatura de A a Z

Aqui está o percurso **completo e real** de uma leitura de temperatura, do sensor até o gráfico no dashboard:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. SENSOR (ESP32 ou Simulador)                                         │
│                                                                         │
│     Publica via MQTT no tópico:                                         │
│     sensors/room/room-101/temperature                                   │
│     Payload: {"value": 24.3, "timestamp": "2026-05-24T23:00:00Z"}      │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │  paho-mqtt (QoS 1)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. MOSQUITTO BROKER (:1883)                                            │
│                                                                         │
│     Recebe e repassa a mensagem para todos os subscribers.              │
│     O backend está subscrito via wildcard: sensors/room/+/temperature   │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. MQTT HANDLER — backend/app/mqtt/handlers.py                         │
│                                                                         │
│     O callback é chamado em uma thread paho separada.                   │
│     Usa asyncio.run_coroutine_threadsafe() para submeter o             │
│     processamento ao loop asyncio do FastAPI sem criar um loop novo     │
│     (solução para o problema de thread-safety com asyncpg).             │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. BUSINESS RULES ENGINE — backend/app/ml/business_rules.py            │
│                                                                         │
│     RuleContext é montado com: valor do sensor, presença, setpoint,    │
│     override manual, horário atual, consumo diário acumulado.           │
│     Cada regra (RN01-RN10) é avaliada em sequência.                    │
│     Output: lista de RuleAction {type: "power_off"|"create_alert"|...} │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  5. PERSISTÊNCIA — PostgreSQL via SQLAlchemy 2.0                        │
│                                                                         │
│     SensorData é inserido na tabela sensor_data.                        │
│     Comandos gerados são inseridos em commands (auditoria completa).    │
│     Alertas são inseridos em alerts.                                    │
│     O dispositivo tem seu status atualizado para ONLINE.                │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  6. REST API — FastAPI serve os dados                                   │
│                                                                         │
│     GET /api/v1/sensors/{id}/data?period=1h                             │
│     GET /api/v1/alerts?active_only=true                                 │
│     Resposta validada por Pydantic, envelope {data, meta, links}.       │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │  HTTP + Bearer JWT
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  7. REACT DASHBOARD (:3000)                                             │
│                                                                         │
│     Polling de 10s via Axios com interceptor JWT automático.            │
│     Recharts renderiza o gráfico de temperatura em tempo real.          │
│     Zustand gerencia autenticação e persiste no localStorage.           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 🔴 Para que serve o Redis? (Desmistificando o componente)

O Redis pode parecer um componente extra desnecessário à primeira vista. Aqui estão os dois motivos **concretos** pelos quais ele existe:

**1. Blacklist de Tokens JWT (Logout Real)**

JWT é stateless por natureza — uma vez emitido, o token é válido até expirar. Sem Redis, um usuário demitido que clicou "Logout" ainda conseguiria acessar a API com o token antigo por até 60 minutos.

```python
# backend/app/api/v1/auth.py — rota POST /auth/logout
token = credentials.credentials
payload = decode_token(token)
ttl = max(1, int(payload["exp"] - time.time()))
await redis.setex(f"blacklist:{token[:32]}", ttl, "1")
# Cada request protegido verifica: se estiver na blacklist → 401
```

**2. Cache de Leituras Recentes (Alivia o PostgreSQL)**

Endpoints que o dashboard consulta a cada 10 segundos (como `/sensors/{id}/latest`) podem ser servidos diretamente do Redis, evitando uma query SQL a cada request. Em uma apresentação com muitos acessos simultâneos, isso mantém a API respondendo rápido.

---

### 🏗️ Por que Monorrepositório?

Todo o código (backend, frontend, IoT, infra) vive em uma única pasta e é orquestrado por um único `docker-compose.yml`. Essa escolha foi deliberada para a ExpoTech:

| Vantagem | Impacto na equipe |
|----------|-------------------|
| **Contexto único na IDE** | A IDE vê todo o projeto — autocomplete cruza frontend com backend |
| **Um `docker compose up`** | Qualquer integrante sobe o ambiente completo em 2 minutos |
| **CI/CD simples** | Um único pipeline testa e faz deploy de tudo |
| **Rastreabilidade** | Um commit pode abranger mudança de API + frontend + testes juntos |

---

## 🛠️ Guia de Hardware de Bancada

> Esta seção é para quem quer ligar um **ESP32 físico** ao sistema. Se você quer só rodar o simulador, pode pular para o [Setup Local](#-setup-local-em-3-passos).

### Componentes Necessários (1 nó de teste)

| Componente | Função no Sistema | Quantidade |
|------------|-------------------|------------|
| **ESP32 DevKit v1** | Microcontrolador Wi-Fi com MQTT | 1 |
| **BME280** (I2C, 3.3V) | Temperatura + Umidade + Pressão | 1 |
| **HC-SR501** (PIR) | Sensor de presença (detecção de movimento) | 1 |
| **LED IR 940nm** (5mm) | Emite sinal infravermelho para simular AC | 1 |
| **Resistor 330 Ω** | Limitador de corrente para o LED IR | 1 |
| Protoboard + Jumpers | Montagem | — |

---

### Diagrama de Ligação Elétrica

```
ESP32 DevKit v1
┌──────────────────────────────────────────────────────┐
│                                                      │
│  3V3  ──────────────────────── VCC (BME280)          │
│  GND  ──┬───────────────────── GND (BME280)          │
│         ├───────────────────── GND (HC-SR501)        │
│         └───────────────────── GND (cátodo LED IR)   │
│                                                      │
│  GPIO 21 (SDA) ─────────────── SDA (BME280)          │
│  GPIO 22 (SCL) ─────────────── SCL (BME280)          │
│                                                      │
│  5V    ─────────────────────── VCC (HC-SR501)*       │
│  GPIO 13 ───────────────────── OUT (HC-SR501)        │
│                                                      │
│  GPIO 4  ── 330Ω ──────────── Anodo (+) LED IR       │
│                                                      │
└──────────────────────────────────────────────────────┘

* O HC-SR501 exige 5V. Use o pino VIN (5V) ou alimentação externa.
```

> **Dica:** O BME280 deve ter o endereço I2C `0x76` (padrão). Se o seu módulo usa `0x77`, ajuste no firmware.

---

### Tópicos que o ESP32 deve publicar

```cpp
// No firmware Arduino/ESP-IDF do ESP32:
// Substitua "room-101" pelo ID da sua sala cadastrada no sistema

// Temperatura (BME280)
client.publish("sensors/room/room-101/temperature",
  "{\"value\": 24.3, \"timestamp\": \"2026-05-24T23:00:00Z\"}");

// Umidade (BME280)
client.publish("sensors/room/room-101/humidity",
  "{\"value\": 62.1, \"timestamp\": \"2026-05-24T23:00:00Z\"}");

// Presença (HC-SR501: 1 = detectou movimento, 0 = ausência)
client.publish("sensors/room/room-101/presence",
  "{\"value\": 1, \"timestamp\": \"2026-05-24T23:00:00Z\"}");

// Para receber comandos do backend (ligar/desligar/setpoint):
client.subscribe("devices/ac/{device_uuid}/commands");
```

---

### 📷 O "Truque da Câmera do Celular" — Validando o IR sem AC

O LED IR emite luz **infravermelha invisível ao olho humano**, mas visível pela câmera do celular (que não tem filtro IR). Use isso para confirmar que o sistema está funcionando:

1. Abra a **câmera frontal** do celular (a traseira costuma ter filtro IR)
2. Aponte o LED IR para a câmera
3. Acesse o dashboard → Salas → clique **OFF** no controle do AC
4. O backend publica `{"action": "off"}` via MQTT
5. O ESP32 recebe e aciona o LED IR
6. **Na tela do celular você verá o LED piscando em roxo/lilás** — confirmação de que o sinal foi enviado!

Isso permite validar toda a cadeia (Dashboard → API → MQTT → ESP32 → IR) **sem precisar de um aparelho de ar-condicionado real**.

---

### 📺 Testando com TV ou Som Doméstico

O protocolo IR de um controle de AC usa os mesmos pacotes hexadecimais de qualquer aparelho doméstico. Você pode:

1. Apontar o LED IR para uma **TV ou aparelho de som** de casa
2. Codificar o comando POWER OFF da TV no firmware do ESP32 (bibliotecas: `IRremoteESP8266` para Arduino)
3. Quando o backend disparar `RN01 — desligamento por ausência`, a TV apaga

O comportamento é **rigorosamente idêntico** ao de um AC real — a lógica de negócio, o fluxo MQTT e o protocolo IR são os mesmos. Perfeito para apresentação em banca sem precisar carregar um ar-condicionado.

---

## 🌐 Estratégia de Rede para a ExpoTech

### A Filosofia: 100% Local, Túnel sob Demanda

Todo o ecossistema roda **100% local** via Docker Compose no notebook da equipe:

```
Notebook da equipe (Docker):
  ├── PostgreSQL    :5432  (persistência)
  ├── Redis         :6379  (cache e blacklist)
  ├── Mosquitto     :1883  (MQTT broker)
  ├── FastAPI       :8000  (API)
  └── React         :3000  (dashboard)
```

**Vantagens para a ExpoTech:**
- Sem dependência de internet ou nuvem
- Latência mínima (tudo local, sem RTT de datacenter)
- Custo zero
- Funciona mesmo com Wi-Fi instável da feira

---

### 🔗 Conectando o ESP32 Físico ao Docker Local via Ngrok

O problema: o ESP32 precisa conectar ao broker Mosquitto (`localhost:1883`), mas `localhost` de dentro do Wi-Fi da feira não aponta para o notebook. A solução é um **túnel TCP com Ngrok**:

```
ESP32 (Wi-Fi da ExpoTech)
        │
        │  TCP → tcp://0.tcp.sa.ngrok.io:XXXXX  (URL gerada pelo Ngrok)
        ▼
[Ngrok Cloud] ──────────────────────────────→ [Notebook :1883 Mosquitto]
                    túnel TCP criptografado
```

**Passo a passo:**

**1. Crie uma conta gratuita** em [ngrok.com](https://ngrok.com) e copie seu token de autenticação.

**2. Configure o `.env` na raiz do projeto:**
```bash
# .env (já está no .gitignore)
NGROK_AUTHTOKEN=seu_token_aqui
```

**3. Suba o sistema com Ngrok:**
```bash
docker compose up -d
```
O serviço `ngrok` já está definido no `docker-compose.yml` e cria o túnel automaticamente.

**4. Descubra a URL pública do Ngrok:**
```bash
docker compose logs ngrok
# Procure por: "started tunnel" → "url":"tcp://0.tcp.sa.ngrok.io:XXXXX"
```

Ou acesse: `http://localhost:4040` (painel web do Ngrok)

**5. Configure o ESP32** com o endereço gerado:
```cpp
// No firmware do ESP32 — substitua pelos valores reais
const char* mqtt_server = "0.tcp.sa.ngrok.io";  // host ngrok
const int   mqtt_port   = 15672;                 // porta gerada pelo ngrok
const char* mqtt_user   = "";                    // sem auth (dev)
const char* mqtt_pass   = "";
```

**6. Pronto!** O ESP32 físico na bancada da ExpoTech agora conversa com o Mosquitto rodando no Docker do notebook, independentemente de onde os dois estejam conectados na rede.

---

## 🚀 Setup Local em 3 Passos

```bash
# Passo 1 — Clone o repositório
git clone https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git
cd SmartBuilding_ExpoTech

# Passo 2 — Suba tudo (banco, backend, frontend, MQTT, simulador)
docker compose up -d --build
# Aguarde ~30 segundos na primeira vez (baixa imagens e roda migrations)

# Passo 3 — Verifique se o backend inicializou corretamente
docker compose logs backend --tail=20
# Você deve ver: "Application startup complete."
```

### Pontas de acesso

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Dashboard React** | http://localhost:3000 | Interface principal do sistema |
| **Swagger UI** | http://localhost:8000/api/docs | Documentação interativa + testes |
| **ReDoc (local)** | http://localhost:8000/api/redoc | Referência visual da API |
| **ReDoc (GitHub Pages)** | https://jhowsoares.github.io/SmartBuilding_ExpoTech/ | Versão pública |
| **Health Check** | http://localhost:8000/api/v1/health | Status dos subsistemas |
| **Ngrok Dashboard** | http://localhost:4040 | Painel do túnel TCP |

### Comandos úteis do dia a dia

```bash
# Ver logs em tempo real
docker compose logs -f backend
docker compose logs -f simulator

# Verificar status de todos os containers
docker compose ps

# Reiniciar só o backend após mudanças no código
docker compose restart backend

# Repovoar o banco (14 salas + 48 dispositivos + 3 usuários)
docker compose exec backend sh -c "cd /app && python -m scripts.seed_db"

# Rodar migrations manualmente
docker compose exec backend sh -c "cd /app && alembic upgrade head"

# Derrubar tudo (CUIDADO: apaga dados do banco)
docker compose down -v
```

---

## 🔐 Credenciais de Acesso

| Usuário | Senha | Papel | O que pode fazer |
|---------|-------|-------|-----------------|
| `admin@smartbuilding.local` | `admin123` | **Admin** | Tudo: CRUD, controle, treinar ML, gerenciar usuários |
| `operador@smartbuilding.local` | `op123` | **Operador** | Controlar dispositivos, reconhecer alertas |
| `visualizador@smartbuilding.local` | `view123` | **Viewer** | Somente leitura — dashboards e relatórios |

> Essas credenciais são inseridas automaticamente pelo `seed_db.py` na primeira inicialização.

---

## 📄 Contrato da API e Documentação Ativa

### Ecossistema de Documentação

```
docs/
├── openapi.yaml     ← Contrato estruturado em OpenAPI 3.0
│                      Define todos os endpoints, schemas, autenticação
│                      e exemplos de request/response
└── index.html       ← Interface ReDoc compilada estática
                       Hospedada no GitHub Pages
```

### Três interfaces, um propósito

| Interface | URL | Quando usar |
|-----------|-----|-------------|
| **Swagger UI** | `localhost:8000/api/docs` | **Para testar** — executa requisições reais com autenticação |
| **ReDoc (local)** | `localhost:8000/api/redoc` | **Para ler** — navegação elegante e referência de schemas |
| **ReDoc (GitHub Pages)** | https://jhowsoares.github.io/SmartBuilding_ExpoTech/ | **Para apresentar** — documentação pública, sem precisar ligar o servidor |

> **Importante:** O ReDoc no GitHub Pages é somente leitura — ele **não executa** requisições. Use o Swagger UI para testar rotas em tempo real.

---

## 🧪 Testando a API

### Via Swagger UI (Recomendado para Banca)

**Passo 1 — Obtenha o token:**
1. Abra http://localhost:8000/api/docs
2. Seção **Auth** → `POST /auth/login` → **Try it out**
3. Cole no body:
```json
{
  "email": "admin@smartbuilding.local",
  "password": "admin123"
}
```
4. Clique **Execute** e copie o `access_token` da resposta

**Passo 2 — Autentique:**
1. Clique no botão **Authorize** (canto superior direito, ícone de cadeado)
2. Cole o token no campo `HTTPBearer`
3. Clique **Authorize** → **Close**

**Passo 3 — Execute qualquer rota.** O cadeado aparece fechado em todos os endpoints.

---

### Via curl (Linux/macOS/WSL)

```bash
# Login e salvar token numa variável
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@smartbuilding.local","password":"admin123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Listar salas
curl -s http://localhost:8000/api/v1/rooms \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Ligar um AC (substitua {device_id} pelo UUID real de GET /devices)
curl -s -X POST "http://localhost:8000/api/v1/devices/{device_id}/control" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "on"}' | python -m json.tool

# Ajustar temperatura para 23°C
curl -s -X POST "http://localhost:8000/api/v1/devices/{device_id}/control" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "setpoint", "value": 23.0}' | python -m json.tool

# Treinar modelo de ML (requer admin)
curl -s -X POST http://localhost:8000/api/v1/predictions/train \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Predição das próximas 24h
curl -s http://localhost:8000/api/v1/predictions/24h \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

### Endpoints Principais

**Base URL:** `http://localhost:8000/api/v1`

#### Autenticação
| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `POST` | `/auth/login` | Login → JWT | — |
| `POST` | `/auth/refresh` | Renovar access token | — |
| `POST` | `/auth/logout` | Revogar token (Redis blacklist) | Bearer |

#### Sensores IoT
| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/sensors` | Listar sensores registrados | Bearer |
| `GET` | `/sensors/{id}/data?period=1h` | Histórico de leituras | Bearer |
| `GET` | `/sensors/{id}/latest` | Leitura mais recente | Bearer |
| `POST` | `/sensors/data` | Ingestão de dado IoT | Token estático |

#### Dispositivos (AC e Sensores)
| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/devices` | Listar dispositivos | Bearer |
| `POST` | `/devices` | Cadastrar dispositivo | Admin |
| `PATCH` | `/devices/{id}` | Atualizar dispositivo | Admin |
| `DELETE` | `/devices/{id}` | Desativar (soft delete) | Admin |
| `POST` | `/devices/{id}/control` | Ligar / Desligar / Setpoint | Operador+ |

#### Salas
| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/rooms` | Listar salas | Bearer |
| `POST` | `/rooms` | Criar sala | Admin |
| `GET` | `/rooms/{id}` | Detalhes da sala | Bearer |
| `GET` | `/rooms/{id}/commands` | Histórico de comandos | Bearer |
| `DELETE` | `/rooms/{id}` | Remover sala | Admin |

#### Alertas
| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/alerts?active_only=true` | Alertas ativos | Bearer |
| `POST` | `/alerts/{id}/acknowledge` | Reconhecer alerta | Operador+ |
| `POST` | `/alerts/{id}/resolve` | Resolver alerta | Operador+ |
| `GET` | `/alerts/history?days=30` | Histórico | Bearer |

#### Consumo e Machine Learning
| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/consumption?period=24h` | Histórico de consumo kWh | Bearer |
| `GET` | `/predictions/24h` | Predição próximas 24h | Bearer |
| `POST` | `/predictions/train` | Retreinar modelo ML | Admin |

#### Usuários e Saúde
| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/users` | Listar usuários | Admin |
| `POST` | `/users` | Criar usuário | Admin |
| `PUT` | `/users/{id}` | Atualizar usuário | Admin |
| `DELETE` | `/users/{id}` | Remover usuário | Admin |
| `GET` | `/health` | Status de todos os subsistemas | — |

---

## 🧠 Regras de Negócio

Todas as regras vivem em `backend/app/ml/business_rules.py` e são avaliadas a cada mensagem MQTT recebida, dentro de um `RuleContext` imutável.

| ID | Regra | Parâmetro | Arquivo de Implementação |
|----|-------|-----------|--------------------------|
| **RN01** | Desligamento automático após **15 min** sem presença detectada | `_ABSENCE_TIMEOUT_MIN = 15` | `business_rules.py → _rn01_absence_auto_off()` |
| **RN02** | Bloqueio do AC com janela aberta por mais de **5 min** | `_WINDOW_BLOCK_MIN = 5` | `business_rules.py → _rn02_window_open_block()` |
| **RN03** | Setpoint mantido entre **23°C e 25°C** (faixa de conforto) | `_IDEAL_TEMP_MIN/MAX` | `business_rules.py → _rn03_ideal_temperature()` |
| **RN04** | Comando manual suspende automações por **30 min** (override) | `_MANUAL_OVERRIDE_MIN = 30` | `device_service.py → mark_manual_override()` |
| **RN05** | Alerta quando consumo diário supera **50 kWh** por dispositivo | `_CONSUMPTION_ALERT_KWH = 50` | `business_rules.py → _rn05_consumption_alert()` |
| **RN06** | AC não liga fora do horário **07h–21h** | `_OPERATING_START/END` | `business_rules.py → _rn06_operating_hours()` |
| **RN07** | Modelo ML retreinado sob demanda via `POST /predictions/train` | — | `ml/predictor.py → train()` |
| **RN08** | Leituras fora da faixa física (ex: temp < 5°C ou > 55°C) são descartadas | `_TEMP_ANOMALY_MIN/MAX` | `business_rules.py → _rn08_validate_sensor()` |
| **RN09** | Toda ação (login, controle, alerta) gera um registro em `audit_logs` | — | `repositories/audit_repository.py → log()` |
| **RN10** | Setpoint adaptativo para eficiência energética (+0.15 kW por grau acima de 24°C) | `_KW_POR_GRAU_ACIMA_IDEAL` | `consumption.py → _estimate_kwh()` |

### Como a IA usa o histórico para predições

```python
# backend/app/ml/predictor.py (simplificado)
#
# Features do modelo:
#   - Hora do dia (0-23)
#   - Dia da semana (0-6)
#   - Temperatura média da última hora
#   - Umidade média da última hora
#   - Percentual de ocupação (presença detectada / total de leituras)
#
# O modelo RandomForestRegressor é treinado com os dados reais
# acumulados no PostgreSQL e retorna kWh previstos por hora.
# R² > 0.85 indica boa aderência ao padrão real do edifício.
```

---

## 📁 Estrutura do Projeto

```
SmartBuilding/
│
├── backend/                          # FastAPI + ML + MQTT
│   ├── app/
│   │   ├── api/v1/                   # Endpoints REST
│   │   │   ├── auth.py               #   POST /auth/login|refresh|logout
│   │   │   ├── devices.py            #   CRUD + POST /control
│   │   │   ├── rooms.py              #   CRUD + GET /commands
│   │   │   ├── sensors.py            #   GET /data, POST /data (IoT)
│   │   │   ├── alerts.py             #   acknowledge, resolve, history
│   │   │   ├── consumption.py        #   histórico kWh estimado
│   │   │   ├── predictions.py        #   predição 24h + train
│   │   │   ├── users.py              #   CRUD de usuários
│   │   │   └── health.py             #   subsystems check
│   │   │
│   │   ├── core/
│   │   │   ├── config.py             #   Pydantic Settings (env vars)
│   │   │   ├── security.py           #   JWT create/decode/verify
│   │   │   ├── deps.py               #   get_current_user, require_admin
│   │   │   └── exceptions.py         #   RFC 7807 Problem Details
│   │   │
│   │   ├── db/
│   │   │   ├── base.py               #   DeclarativeBase SQLAlchemy
│   │   │   └── database.py           #   async engine, sessions, ping_db
│   │   │
│   │   ├── ml/
│   │   │   ├── business_rules.py     #   Motor de regras RN01-RN10
│   │   │   ├── predictor.py          #   RandomForestRegressor
│   │   │   └── features.py           #   Pipeline de features
│   │   │
│   │   ├── models/                   #   ORM — tabelas PostgreSQL
│   │   │   ├── user.py               #   users (RBAC)
│   │   │   ├── room.py               #   rooms
│   │   │   ├── device.py             #   devices (AC, sensores)
│   │   │   ├── sensor_data.py        #   sensor_data (time-series)
│   │   │   ├── alert.py              #   alerts
│   │   │   ├── command.py            #   commands (auditoria de controle)
│   │   │   └── audit_log.py          #   audit_logs (rastreabilidade)
│   │   │
│   │   ├── mqtt/
│   │   │   ├── client.py             #   MQTTClient singleton (paho-mqtt)
│   │   │   └── handlers.py           #   async callback + rules engine
│   │   │
│   │   ├── repositories/             #   Repository Pattern
│   │   ├── schemas/                  #   Pydantic v2 (validação)
│   │   └── services/                 #   Casos de uso
│   │
│   ├── alembic/versions/             #   Migrations versionadas
│   ├── scripts/seed_db.py            #   14 salas + 48 dispositivos + 3 users
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                         # React 18 + Vite + TailwindCSS
│   ├── src/
│   │   ├── pages/                    #   Dashboard, Salas, Alertas, Relatórios...
│   │   ├── components/               #   Layout, Sidebar, Header, ErrorBoundary
│   │   ├── services/api.js           #   Axios + interceptors JWT automáticos
│   │   └── store/authStore.js        #   Zustand (auth + RBAC)
│   ├── nginx.conf                    #   Proxy /api → backend + SPA fallback
│   └── Dockerfile
│
├── simulator/
│   └── simulator.py                  # 14 salas, publica a cada 5s via MQTT
│
├── mosquitto/
│   └── config/mosquitto.conf         # Broker MQTT (porta 1883 + WebSocket 9001)
│
├── Rede/                             # Serviços legados de rede (preservados)
│   ├── clock/                        # Sincronização de tempo
│   ├── server/                       # Flask legado
│   ├── client/                       # Cliente de rede
│   ├── scheduler/                    # Agendamento
│   └── sensor/                       # Sensor legado
│
├── docs/                             # Documentação estática (GitHub Pages)
│   ├── openapi.yaml                  # Contrato OpenAPI 3.0
│   └── index.html                    # ReDoc compilado
│
├── .env                              # Variáveis sensíveis (NÃO commitado)
├── docker-compose.yml                # Orquestra todos os serviços
└── README.md
```

---

## 📡 Tópicos MQTT

### Publicados pelos Sensores (ESP32 ou Simulador → Mosquitto → Backend)

```
sensors/room/{room_id}/temperature
sensors/room/{room_id}/humidity
sensors/room/{room_id}/presence
sensors/room/{room_id}/window

Payload padrão:
{
  "value": 24.3,
  "timestamp": "2026-05-24T23:00:00Z",
  "tick": 42
}

Onde:
  room_id   = identificador da sala (ex: "room-101")
  value     = temperatura (°C) | umidade (%) | presença (0 ou 1) | janela (0 ou 1)
  tick      = contador de sequência (detecta pacotes perdidos)
```

### Publicados pelo Backend → Dispositivos AC

```
devices/ac/{device_id}/commands

Payload:
{
  "action": "on" | "off" | "setpoint",
  "value": 23.0   (apenas para action="setpoint")
}
```

### Publicados pelos ACs → Backend (Feedback de Confirmação)

```
devices/ac/{device_id}/feedback

Payload:
{
  "power": "on" | "off",
  "setpoint": 23.0,
  "timestamp": "2026-05-24T23:00:05Z"
}
```

---

## ⚙️ Variáveis de Ambiente

### `backend/.env` — Configuração do Backend

| Variável | Descrição | Padrão de Desenvolvimento |
|----------|-----------|--------------------------|
| `DATABASE_URL` | URL asyncpg do PostgreSQL | `postgresql+asyncpg://jhonata:expo_PSW_1@postgres:5432/expotech_db` |
| `SYNC_DATABASE_URL` | URL psycopg2 para Alembic | `postgresql+psycopg2://...` |
| `JWT_SECRET` | Segredo JWT (mín. 32 chars) | **Trocar em produção** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do access token | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiração do refresh token | `7` |
| `REDIS_URL` | Conexão com Redis | `redis://redis:6379/0` |
| `MQTT_BROKER` | Host do broker MQTT | `mqtt` |
| `MQTT_PORT` | Porta MQTT | `1883` |
| `CORS_ORIGINS` | Origens permitidas pelo browser | `*` (dev) |
| `ENERGIA_TARIFA_KWH_BRL` | Tarifa de energia em R$/kWh | `0.75` |
| `SENSOR_SERVICE_TOKEN` | Token para ingestão IoT | `sensor-service-token-dev` |

### `.env` — Raiz do Projeto (Ngrok)

| Variável | Descrição |
|----------|-----------|
| `NGROK_AUTHTOKEN` | Token da conta Ngrok (obtido em ngrok.com/dashboard) |

> O arquivo `.env` está listado no `.gitignore` — **nunca** commite secrets.

---

## 👥 Equipe

| Integrante | Papel | Responsabilidades Técnicas |
|------------|-------|---------------------------|
| **Jhonata Soares** | Backend Lead | FastAPI, PostgreSQL, SQLAlchemy, JWT/RBAC, API REST design, Deploy Docker |
| **João Arnaldo** | IoT & MQTT | Mosquitto, Simulador Python, firmware ESP32, protocolo IR, Ngrok |
| **Rickelmy** | IA & Dados | scikit-learn, pipeline ML, motor de regras RN01-RN10, análise de consumo |
| **Felipe Pardinho** | Frontend | React 18, Tailwind, Recharts, UX/UI, Zustand, design system |
| **Claudio Rodrigues** | DevOps & QA | Docker Compose, Alembic migrations, seed scripts, testes de integração |

---

<div align="center">

**Smart Building · ExpoTech 2026**

*Documentação atualizada em 24/05/2026*

[Swagger UI](http://localhost:8000/api/docs) · [ReDoc](https://jhowsoares.github.io/SmartBuilding_ExpoTech/) · [GitHub](https://github.com/Jhowsoares/SmartBuilding_ExpoTech)

</div>
