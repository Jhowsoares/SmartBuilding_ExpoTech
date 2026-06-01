# Mapa da documentação — Smart Building

Referência única: **onde está cada arquivo** e **qual página HTML o exibe** na GitHub Pages.

---

## Páginas da apresentação (HTML)

| Página | URL (Pages) | Público |
|--------|-------------|---------|
| [index.html](index.html) | `/` | Landing ExpoTech |
| [engenharias.html](engenharias.html) | `/engenharias.html` | Panorama integrador + cronograma |
| [civil.html](civil.html) | `/civil.html` | Eng. Civil — maquete e vista 3D |
| [eletrica.html](eletrica.html) | `/eletrica.html` | Eng. Elétrica — sensores e MQTT |
| [producao.html](producao.html) | `/producao.html` | Eng. Produção — financeiro |
| [computacao.html](computacao.html) | `/computacao.html` | Eng. Computação — stack e links |
| [sistema.html](sistema.html) | `/sistema.html` | Arquitetura técnica completa |
| [api.html](api.html) | `/api.html` | ReDoc (OpenAPI) |
| [documentacao.html](documentacao.html) | `/documentacao.html` | **Este índice interativo** |

---

## Projeto integrador (`engenharias/`)

| Markdown | Conteúdo | Página HTML |
|----------|----------|-------------|
| [engenharias/README.md](engenharias/README.md) | Visão multidisciplinar | [engenharias.html](engenharias.html) |
| [engenharias/civil.md](engenharias/civil.md) | Civil — resumo curado | [civil.html](civil.html) |
| [engenharias/eletrica.md](engenharias/eletrica.md) | Elétrica — resumo curado | [eletrica.html](eletrica.html) |
| [engenharias/producao.md](engenharias/producao.md) | Produção — resumo curado | [producao.html](producao.html) |
| [engenharias/computacao.md](engenharias/computacao.md) | Computação — resumo curado | [computacao.html](computacao.html) |
| [engenharias/cronograma.md](engenharias/cronograma.md) | Cronograma web | [engenharias.html#cronograma](engenharias.html#cronograma) |
| [engenharias/equipe-integrador.md](engenharias/equipe-integrador.md) | Equipes | [engenharias.html#equipe](engenharias.html#equipe) |

### Entregáveis originais (`engenharias/entregaveis/`)

| Pasta / PDF | Área | Página HTML |
|-------------|------|-------------|
| [civil/](engenharias/entregaveis/civil/) | Relatório + vista 3D (`.md`) | [civil.html](civil.html) |
| [eletrica/](engenharias/entregaveis/eletrica/) | PDF formal (pendente) | [eletrica.html](eletrica.html) |
| [producao/](engenharias/entregaveis/producao/) | Relatório financeiro | [producao.html](producao.html) |
| [computacao/](engenharias/entregaveis/computacao/) | PDFs de arquitetura | [computacao.html](computacao.html) |
| [em_pdf/](engenharias/entregaveis/em_pdf/) | PDFs oficiais | [engenharias.html#entregaveis](engenharias.html#entregaveis) |

---

## Sistema técnico (`sistema/`)

| Markdown | Seção em sistema.html |
|----------|------------------------|
| [architecture.md](sistema/architecture.md) | `#arquitetura` |
| [project-structure.md](sistema/project-structure.md) | `#arquitetura` |
| [api.md](sistema/api.md) | `#api` + [api.html](api.html) |
| [mqtt.md](sistema/mqtt.md) | `#mqtt` |
| [business-rules.md](sistema/business-rules.md) | `#regras` |
| [hardware-esp32.md](sistema/hardware-esp32.md) | `#hardware` |
| [network-expotech.md](sistema/network-expotech.md) | `#ngrok` |
| [team.md](sistema/team.md) | `#equipe` |
| [deprecation-policy.md](sistema/deprecation-policy.md) | [api.html](api.html) (governança) |

Índice da pasta: [sistema/README.md](sistema/README.md)

---

## Guias (`guias/`)

| Markdown | Onde aparece |
|----------|--------------|
| [setup.md](guias/setup.md) | [sistema.html#setup](sistema.html#setup) |
| [environment.md](guias/environment.md) | [sistema.html#setup](sistema.html#setup) |
| [repositorio.md](guias/repositorio.md) | Meta (clone / limpeza) |

Índice da pasta: [guias/README.md](guias/README.md)

---

## Contrato e API

| Arquivo | Página |
|---------|--------|
| [openapi.yaml](openapi.yaml) | [api.html](api.html) (ReDoc) |
| [spectral.yml](../spectral.yml) | CI — lint do contrato (raiz do repo) |

---

## Material interno (não na feira)

| Pasta | Uso |
|-------|-----|
| [rascunho/](rascunho/) | Defesa, questionário AVA, material de aula — **não publicado na Pages** |

---

## Arquivos removidos da raiz de `docs/`

Estes atalhos redundantes foram consolidados nas pastas acima:

`architecture.md` · `setup.md` · `environment.md` · `repositorio.md` · `api.md` · `mqtt.md` · `business-rules.md` · `hardware-esp32.md` · `network-expotech.md` · `project-structure.md` · `team.md` · `deprecation-policy.md`

Use este mapa ou [documentacao.html](documentacao.html) em vez deles.
