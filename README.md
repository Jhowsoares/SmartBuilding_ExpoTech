# 🏢 Smart Building — Sistema de Inteligência e Automação Predial

[![API Docs](https://img.shields.io/badge/API-Swagger-blue?logo=swagger)](http://localhost:8000/api/docs)
[![Docs](https://img.shields.io/badge/Docs-GitHub%20Pages-informational)](https://jhowsoares.github.io/SmartBuilding_ExpoTech/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](backend/)

> *"Economize energia, respeite o conforto, automatize com inteligência."*

---

## 🚀 Visão Geral do Projeto

O **Smart Building** é um ecossistema completo de Internet das Coisas (IoT) e automação predial focado em **eficiência energética** e **controle inteligente de climatização**. O sistema integra dispositivos físicos (microcontroladores), mensageria em tempo real, uma API backend robusta e um painel de controle interativo para monitoramento de ambientes.

---

## 📐 Arquitetura do Sistema

O fluxo de dados da aplicação distribui-se em camadas desacopladas para garantir escalabilidade e resiliência:

```text
[ ESP32 / Simulador (C++) ] 
       │ (MQTT Pub/Sub)
       ▼
[ Broker Mosquitto (MQTT) ] 
       │
       ▼
[ Backend FastAPI (Python) ] ──(Persistência)──> [ Banco de Dados / SQLite ]
       │
       ├─ (REST API / Swagger)
       ▼
[ Frontend Dashboard (JavaScript) ]

```

---

## 🛠️ Stack Tecnológica

* **Backend:** Python, FastAPI, SQLAlchemy, Pydantic, Uvicorn.
* **Mensageria & IoT:** MQTT (Eclipse Mosquitto), C++ (Firmware ESP32).
* **Frontend:** JavaScript (ES6+), HTML5, CSS3, Dashboard Interativo.
* **Infraestrutura:** Docker, Docker Compose, CI/CD via GitHub Actions.
* **Testes & Qualidade:** Pytest, OpenAPI/Swagger UI, Spectral.

---

## ⚙️ Como Executar o Projeto (Quickstart)

Certifique-se de ter o [Docker](https://www.docker.com/) e o Docker Compose instalados em sua máquina.

1. **Clone o repositório:**
```bash
git clone [https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git](https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git)
cd SmartBuilding_ExpoTech

```


2. **Suba o ambiente completo via Docker Compose:**
```bash
docker compose up -d --build

```


3. **Acesse os serviços locais:**
* **Dashboard Frontend:** [http://localhost:3000](http://localhost:8000) *(ou porta correspondente configurada)*
* **Documentação da API (Swagger):** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
* **Credenciais padrão de acesso:** `admin@smartbuilding.local` / `admin123`



---

## 📚 Documentação Técnica

Para detalhes aprofundados sobre a arquitetura de rede, contratos de API e regras de negócio:

* Consulte o Guia de Setup e Primeiro Uso
* Acesse a [Landing Page da Documentação (GitHub Pages)](https://jhowsoares.github.io/SmartBuilding_ExpoTech/)

---

## 👨‍💻 Autor

Desenvolvido por **Jhonata Viana Soares**.

* [GitHub](https://github.com/Jhowsoares)

