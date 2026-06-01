# Documentação — Smart Building

Índice central da documentação do projeto **ECO-API / Smart Building** (ExpoTech 2026).

---

## Projeto integrador (visão multidisciplinar)

| Documento | Conteúdo |
|-----------|----------|
| **[Visão geral das engenharias](engenharias/README.md)** | Como Civil, Elétrica, Produção e Computação se integram |
| **[Eng. Civil](engenharias/civil.md)** | Infraestrutura, conforto térmico, maquete |
| **[Eng. Elétrica](engenharias/eletrica.md)** | Sensores, Arduino/Bluetooth, automação física |
| **[Eng. Produção](engenharias/producao.md)** | Viabilidade financeira, CAPEX/OPEX, ROI |
| **[Eng. Computação](engenharias/computacao.md)** | API, dashboard, MQTT, ML — resumo + links |
| **[Cronograma integrado](engenharias/cronograma.md)** | Tarefas por área (versão web) |
| **[Equipe integradora](engenharias/equipe-integrador.md)** | Integrantes de todas as engenharias |

> **Site (GitHub Pages):** [Visão integrada](https://jhowsoares.github.io/SmartBuilding_ExpoTech/engenharias.html) · [Documentação técnica](https://jhowsoares.github.io/SmartBuilding_ExpoTech/)

---

## Guias (primeiro uso)

| Documento | Conteúdo |
|-----------|----------|
| **[Setup e primeiro uso](guias/setup.md)** | Docker para iniciantes, passo a passo |
| **[Variáveis de ambiente](guias/environment.md)** | `.env` e configurações |
| **[Repositório — tamanho](guias/repositorio.md)** | Por que o clone parece pesado, como limpar |

---

## Sistema (documentação técnica)

| Documento | Conteúdo |
|-----------|----------|
| **[Arquitetura](sistema/architecture.md)** | Stack, diagrama, fluxo de dados |
| **[Estrutura do projeto](sistema/project-structure.md)** | Pastas, serviços Docker |
| **[API](sistema/api.md)** | Swagger, credenciais, endpoints |
| **[MQTT](sistema/mqtt.md)** | Tópicos e payloads |
| **[Regras de negócio](sistema/business-rules.md)** | RN01–RN10 e ML |
| **[Hardware ESP32](sistema/hardware-esp32.md)** | Pinagem, firmware, ponte Bluetooth |
| **[Rede / ExpoTech](sistema/network-expotech.md)** | Ngrok, ESP32 remoto |
| **[Equipe CS](sistema/team.md)** | Integrantes de Computação |
| **[Política de depreciação](sistema/deprecation-policy.md)** | Ciclo de vida da API |

---

## Arquivos na raiz de `docs/`

| Arquivo | Uso |
|---------|-----|
| `index.html` | **Apresentação na feira** (GitHub Pages — landing) |
| `engenharias.html` | Panorama integrador + cronograma + PDFs |
| `sistema.html` | Documentação técnica completa (C4, API, MQTT, RN…) |
| `civil.html` | Página Eng. Civil (maquete / entregáveis) |
| `api.html` | ReDoc interativo |
| `openapi.yaml` | Contrato OpenAPI 3.1 |
| `setup.md`, `architecture.md`, … | **Atalhos** → conteúdo em `guias/` e `sistema/` |

> **Feira:** use as páinas `.html` — elas não foram removidas. Os `.md` na raiz redirecionam para as pastas organizadas.
