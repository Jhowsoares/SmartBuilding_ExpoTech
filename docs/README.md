# Documentação — Smart Building

Índice central da documentação do projeto **ECO-API / Smart Building** (ExpoTech 2026).

---

## Projeto integrador (visão multidisciplinar)

| Documento | Conteúdo | Página na feira |
|-----------|----------|-----------------|
| **[Visão geral das engenharias](engenharias/README.md)** | Como Civil, Elétrica, Produção e Computação se integram | [engenharias.html](engenharias.html) |
| **[Eng. Civil](engenharias/civil.md)** | Infraestrutura, conforto térmico, maquete | [civil.html](civil.html) |
| **[Eng. Elétrica](engenharias/eletrica.md)** | Sensores, Arduino/Bluetooth, automação física | [eletrica.html](eletrica.html) |
| **[Eng. Produção](engenharias/producao.md)** | Viabilidade financeira, CAPEX/OPEX, ROI | [producao.html](producao.html) |
| **[Eng. Computação](engenharias/computacao.md)** | API, dashboard, MQTT, ML — resumo + links | [computacao.html](computacao.html) |
| **[Cronograma integrado](engenharias/cronograma.md)** | Tarefas por área (versão web) | [engenharias.html#cronograma](engenharias.html#cronograma) |
| **[Equipe integradora](engenharias/equipe-integrador.md)** | Integrantes de todas as engenharias | [engenharias.html#equipe](engenharias.html#equipe) |

> **Mapa completo:** [MAPA.md](MAPA.md) · [documentacao.html](documentacao.html)

---

## Guias (primeiro uso)

| Documento | Conteúdo | Página na feira |
|-----------|----------|-----------------|
| **[Setup e primeiro uso](guias/setup.md)** | Docker para iniciantes, passo a passo | [sistema.html#setup](sistema.html#setup) |
| **[Variáveis de ambiente](guias/environment.md)** | `.env` e configurações | [sistema.html#setup](sistema.html#setup) |
| **[Repositório — tamanho](guias/repositorio.md)** | Por que o clone parece pesado, como limpar | [documentacao.html](documentacao.html) |

---

## Sistema (documentação técnica)

| Documento | Conteúdo | Página na feira |
|-----------|----------|-----------------|
| **[Arquitetura](sistema/architecture.md)** | Stack, diagrama, fluxo de dados | [sistema.html#arquitetura](sistema.html#arquitetura) |
| **[Estrutura do projeto](sistema/project-structure.md)** | Pastas, serviços Docker | [sistema.html#arquitetura](sistema.html#arquitetura) |
| **[API](sistema/api.md)** | Swagger, credenciais, endpoints | [api.html](api.html) |
| **[MQTT](sistema/mqtt.md)** | Tópicos e payloads | [sistema.html#mqtt](sistema.html#mqtt) |
| **[Regras de negócio](sistema/business-rules.md)** | RN01–RN10 e ML | [sistema.html#regras](sistema.html#regras) |
| **[Hardware ESP32](sistema/hardware-esp32.md)** | Pinagem, firmware, ponte Bluetooth | [sistema.html#hardware](sistema.html#hardware) |
| **[Rede / ExpoTech](sistema/network-expotech.md)** | Ngrok, ESP32 remoto | [sistema.html#ngrok](sistema.html#ngrok) |
| **[Equipe CS](sistema/team.md)** | Integrantes de Computação | [sistema.html#equipe](sistema.html#equipe) |
| **[Política de depreciação](sistema/deprecation-policy.md)** | Ciclo de vida da API | [api.html](api.html) |

---

## Arquivos na raiz de `docs/` (GitHub Pages)

| Arquivo | Uso |
|---------|-----|
| `index.html` | Landing da feira |
| `engenharias.html` | Panorama integrador + cronograma + PDFs |
| `civil.html` · `eletrica.html` · `producao.html` · `computacao.html` | Uma página por engenharia |
| `sistema.html` | Documentação técnica (C4, API, MQTT, RN…) |
| `api.html` | ReDoc interativo |
| `documentacao.html` | **Mapa Markdown → páginas HTML** |
| `openapi.yaml` | Contrato OpenAPI 3.1 |
| **[MAPA.md](MAPA.md)** | Índice editável (mesmo conteúdo do mapa web) |

### Pastas (conteúdo canônico)

| Pasta | Conteúdo | Índice |
|-------|----------|--------|
| `engenharias/` | Integrador + entregáveis por área | [engenharias/README.md](engenharias/README.md) |
| `sistema/` | Documentação técnica da plataforma | [sistema/README.md](sistema/README.md) |
| `guias/` | Setup, ambiente, repositório | [guias/README.md](guias/README.md) |
| `assets/` | CSS e logo das páginas HTML | — |
| `rascunho/` | Material interno (não na feira) | — |

> Os antigos `.md` soltos na raiz (`architecture.md`, `setup.md`, …) foram removidos — use [MAPA.md](MAPA.md) ou [documentacao.html](documentacao.html).
