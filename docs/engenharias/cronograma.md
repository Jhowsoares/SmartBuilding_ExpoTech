# Cronograma Integrado

Cronograma consolidado das tarefas por engenharia. A versão completa com datas e status está no arquivo Excel original.

---

## Download do cronograma original

| Formato | Arquivo |
|---------|---------|
| **Excel (.xlsb)** | [cronograma-projeto-faculdade.xlsb](entregaveis/cronograma-projeto-faculdade.xlsb) |

**Visualização web:** [GitHub Pages — Cronograma](https://jhowsoares.github.io/SmartBuilding_ExpoTech/engenharias.html#cronograma)

### Atualizar a visualização web

Depois de editar o Excel, rode **um único comando** na raiz do projeto:

```bash
python tools/build_engenharias_page.py
```

Isso lê o `.xlsb`, atualiza `cronograma-data.json` e regenera `engenharias.html`. Requisito: `pip install pyxlsb` (só na primeira vez).

---

## Eng. Civil (6 tarefas)

| # | Tarefa |
|---|--------|
| 1 | Analisar causa raiz da condensação/vazamento e materiais de reparo |
| 2 | Definir e orçar materiais (silicone, isolantes térmicos) |
| 3 | Projeto da maquete (escala, MDF/acrílico/PVC) |
| 4 | Aplicar reparo ou protótipo de contenção |
| 5 | Construir maquete com passagens para fiação e sensores |
| 6 | Finalização estética, testes de estanqueidade e slides |

---

## Eng. Elétrica (5 tarefas)

| # | Tarefa |
|---|--------|
| 1 | Montagem no protoboard / preparação para maquete |
| 2 | Programação e testes iniciais do Arduino |
| 3 | Alinhamento da maquete com Civil |
| 4 | Entrega do Arduino para integração com dashboard |
| 5 | Ajustes finais na maquete com Civil |

---

## Eng. Computação (resumo por frente)

O cronograma de Computação está organizado por desenvolvedor. Principais marcos:

### Backend (Jhonata)
- Estrutura FastAPI + Swagger
- Modelos SQLAlchemy (8 tabelas)
- JWT, CRUD completo, consumo e predições
- Integração MQTT → PostgreSQL

### IoT (João Arnaldo)
- Mosquitto + simulador 14 salas
- Firmware ESP32
- Documentação de tópicos MQTT

### IA & Frontend (Rickelmy / Felipe)
- Pipeline ML + regras RN01–RN10
- Dashboard React (login, relatórios, predições)

### DevOps (Claudio)
- Docker Compose completo
- Seed, testes E2E, documentação README
- Slides e vídeo pitch

> Lista completa com **59 itens** no Excel e na [página web](https://jhowsoares.github.io/SmartBuilding_ExpoTech/engenharias.html#cronograma).

---

## Eng. Produção

Responsável pela **gestão do cronograma integrado** e pelo [relatório financeiro](producao.md).

---

## Dados estruturados

O arquivo [`cronograma-data.json`](cronograma-data.json) contém as tarefas extraídas do Excel para exibição no GitHub Pages (gerado a partir do `.xlsb`).
