<div align="center">

# Smart Building
### Sistema de Controle Inteligente de Ar-Condicionado

**ExpoTech 2026 · Engenharia da Computação**

[![API Docs](https://img.shields.io/badge/API-Swagger_UI-85ea2d?logo=swagger)](http://localhost:8000/api/docs)
[![ReDoc](https://img.shields.io/badge/Docs-GitHub_Pages-orange?logo=readme)](https://jhowsoares.github.io/SmartBuilding_ExpoTech/)
[![Docker](https://img.shields.io/badge/Deploy-Docker_Compose-2496ed?logo=docker)](https://www.docker.com/)

> *"Economize energia, respeite o conforto, automatize com inteligência."*

</div>

---

## Comece aqui

**Primeira vez no projeto?** Siga o guia passo a passo (inclui instalação do Docker, primeiros comandos e solução de problemas comuns):

**[Configuração e Primeiro Uso → docs/setup.md](docs/setup.md)**

Em três comandos, após instalar o Docker Desktop:

```bash
git clone https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git
cd SmartBuilding_ExpoTech
docker compose up -d --build
```

| O quê | URL |
|-------|-----|
| Dashboard | http://localhost:3000 |
| Swagger (testar API) | http://localhost:8000/api/docs |
| Documentação pública | https://jhowsoares.github.io/SmartBuilding_ExpoTech/ |

Login padrão: `admin@smartbuilding.local` / `admin123`

---

## Documentação completa

A documentação foi dividida em arquivos menores para facilitar a leitura e a manutenção.

| Documento | Conteúdo |
|-----------|----------|
| **[Setup e primeiro uso](docs/setup.md)** | Docker para iniciantes, passo a passo, troubleshooting |
| **[Arquitetura](docs/architecture.md)** | Stack, diagrama, fluxo de dados, Redis, monorepo |
| **[Hardware ESP32](docs/hardware-esp32.md)** | Pinagem, firmware, IR, ponte Bluetooth |
| **[Rede / ExpoTech](docs/network-expotech.md)** | Ngrok, ESP32 remoto, IP local |
| **[API](docs/api.md)** | Swagger, credenciais, endpoints, exemplos |
| **[Regras de negócio](docs/business-rules.md)** | RN01–RN10 e ML |
| **[Estrutura do projeto](docs/project-structure.md)** | Pastas, serviços Docker |
| **[MQTT](docs/mqtt.md)** | Tópicos e payloads |
| **[Variáveis de ambiente](docs/environment.md)** | `.env` e configurações |
| **[Equipe](docs/team.md)** | Integrantes e papéis |
| **[Repositório — tamanho](docs/repositorio.md)** | Por que o clone parece pesado, como limpar |

---

## Visão geral (resumo)

O **Smart Building** é uma plataforma IoT para monitoramento e automação de climatização em edifícios corporativos:

- **14 salas simuladas** publicando temperatura, umidade e presença via MQTT a cada 5s
- **10 regras de negócio** (desligamento por ausência, horário comercial, alertas de consumo…)
- **Predição de consumo 24h** com scikit-learn
- **Dashboard React** com controle de AC, relatórios e alertas
- **API REST** documentada (OpenAPI 3, Swagger, ReDoc)

### Stack

FastAPI · PostgreSQL · Redis · Mosquitto MQTT · React 18 · Docker Compose · scikit-learn

---

## Repositório pesado?

Se o clone ou a pasta parecem ter **vários GB**, leia **[docs/repositorio.md](docs/repositorio.md)**.

Resumo:

- O **Git** tinha modelos ML (`.pkl` ~50 MB) versionados — agora estão no `.gitignore`.
- **Imagens Docker** (2–8 GB) não fazem parte do Git; são baixadas no primeiro `docker compose up`.
- Para limpar o histórico Git de arquivos antigos, siga o guia em `docs/repositorio.md`.

---

## Links rápidos

[Swagger UI](http://localhost:8000/api/docs) · [GitHub Pages](https://jhowsoares.github.io/SmartBuilding_ExpoTech/) · [GitHub](https://github.com/Jhowsoares/SmartBuilding_ExpoTech)

---

<div align="center">

**Smart Building · ExpoTech 2026**

Documentação atualizada em maio/2026

</div>
