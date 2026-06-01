<div align="center">

# Smart Building
### Sistema de Controle Inteligente de Ar-Condicionado

**ExpoTech 2026 · Projeto Integrador (4 Engenharias)**

[![API Docs](https://img.shields.io/badge/API-Swagger_UI-85ea2d?logo=swagger)](http://localhost:8000/api/docs)
[![Docs](https://img.shields.io/badge/Docs-GitHub_Pages-orange?logo=readme)](https://jhowsoares.github.io/SmartBuilding_ExpoTech/)
[![Docker](https://img.shields.io/badge/Deploy-Docker_Compose-2496ed?logo=docker)](https://www.docker.com/)

> *"Economize energia, respeite o conforto, automatize com inteligência."*

</div>

---

## Comece aqui

**Primeira vez no projeto?** Siga o guia passo a passo (Docker, primeiros comandos, troubleshooting):

**[Configuração e Primeiro Uso → docs/guias/setup.md](docs/guias/setup.md)**

```bash
git clone https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git
cd SmartBuilding_ExpoTech
docker compose up -d --build
```

| O quê | URL |
|-------|-----|
| Dashboard | http://localhost:3000 |
| Swagger (testar API) | http://localhost:8000/api/docs |
| Documentação técnica (Pages) | https://jhowsoares.github.io/SmartBuilding_ExpoTech/ |
| **Panorama integrador (Pages)** | https://jhowsoares.github.io/SmartBuilding_ExpoTech/engenharias.html |

Login padrão: `admin@smartbuilding.local` / `admin123`

---

## Projeto integrador (visão geral)

Este repositório reúne **Civil, Elétrica, Produção e Computação** em torno da automação de climatização no laboratório de elétrica (subsolo).

| Área | Resumo |
|------|--------|
| **Civil** | Infraestrutura, conforto térmico, maquete |
| **Elétrica** | Sensores, Arduino/Bluetooth, automação física |
| **Produção** | CAPEX/OPEX, ROI, cronograma |
| **Computação** | API, MQTT, ML, dashboard (este repositório) |

**[Visão completa das engenharias → docs/engenharias/README.md](docs/engenharias/README.md)**

---

## Documentação do sistema

| Documento | Conteúdo |
|-----------|----------|
| **[Índice completo](docs/README.md)** | Todos os guias e referências |
| **[Setup](docs/guias/setup.md)** | Docker para iniciantes |
| **[Arquitetura](docs/sistema/architecture.md)** | Stack, diagrama, fluxo de dados |
| **[API](docs/sistema/api.md)** | Swagger, endpoints, exemplos |
| **[MQTT](docs/sistema/mqtt.md)** | Tópicos e payloads |
| **[Regras de negócio](docs/sistema/business-rules.md)** | RN01–RN10 |
| **[Hardware ESP32](docs/sistema/hardware-esp32.md)** | Firmware e pinagem |
| **[Equipe CS](docs/sistema/team.md)** | Integrantes de Computação |
| **[Repositório — tamanho](docs/guias/repositorio.md)** | Clone pesado, como limpar |
| **[Depreciação API](docs/sistema/deprecation-policy.md)** | Ciclo de vida `/v1` |

---

## Visão geral técnica (resumo)

- **14 salas simuladas** via MQTT (telemetria a cada 5s)
- **10 regras de negócio** + predição ML 24h
- **Dashboard React** + **API REST** OpenAPI 3.1
- **Docker Compose** — 6 serviços

**Stack:** FastAPI · PostgreSQL · Redis · Mosquitto · React · scikit-learn

---

## Repositório pesado?

Leia **[docs/guias/repositorio.md](docs/guias/repositorio.md)** — modelos `.pkl` saíram do Git; imagens Docker são baixadas no primeiro `docker compose up`.

---

## Links rápidos

[Swagger UI](http://localhost:8000/api/docs) · [GitHub Pages](https://jhowsoares.github.io/SmartBuilding_ExpoTech/) · [Engenharias (Pages)](https://jhowsoares.github.io/SmartBuilding_ExpoTech/engenharias.html) · [GitHub](https://github.com/Jhowsoares/SmartBuilding_ExpoTech)

---

<div align="center">

**Smart Building · ExpoTech 2026**

Documentação atualizada em maio/2026

</div>
