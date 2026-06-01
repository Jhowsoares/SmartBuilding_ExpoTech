# Projeto Integrador — Visão Multidisciplinar

O **Smart Building** não é apenas uma API: é um projeto integrador da UniFECAF que reúne **quatro engenharias** em torno de um problema real — **eficiência energética e conforto térmico** no laboratório de elétrica (subsolo do prédio principal).

---

## O problema

O ambiente apresenta **condensação, umidade elevada** e **climatização sem controle inteligente**. Isso gera desconforto, desperdício de energia e desgaste dos equipamentos de ar-condicionado.

---

## A solução integrada

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  CIVIL      │     │  ELÉTRICA    │     │ COMPUTAÇÃO  │     │  PRODUÇÃO    │
│  Maquete +  │ ──► │  Sensores +  │ ──► │  API +      │ ──► │  Viabilidade │
│  infra fís. │     │  Arduino/BT  │     │  Dashboard  │     │  financeira  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
       │                    │                    │                    │
       └────────────────────┴────────────────────┴────────────────────┘
                    Laboratório de elétrica (subsolo)
                    Automação de climatização + monitoramento
```

| Área | Papel no projeto | Documentação |
|------|------------------|--------------|
| **Eng. Civil** | Análise da edificação, conforto térmico, maquete de apresentação | [civil.md](civil.md) |
| **Eng. Elétrica** | Captura física de dados (temperatura, presença), automação do AC | [eletrica.md](eletrica.md) |
| **Eng. Computação** | Plataforma digital: API REST, MQTT, ML, dashboard web | [computacao.md](computacao.md) |
| **Eng. Produção** | Análise de custos, ROI, cronograma e riscos | [producao.md](producao.md) |

---

## Documentação curada × entregáveis originais

Para facilitar a avaliação, organizamos a documentação em **dois níveis**:

| Tipo | Onde fica | Para quê |
|------|-----------|----------|
| **Documentação curada** | Arquivos `.md` nesta pasta (`civil.md`, `producao.md`, etc.) | Leitura rápida, coerente e integrada — ideal para GitHub e GitHub Pages |
| **Entregáveis originais** | Pasta [`entregaveis/`](entregaveis/) | Documentos como cada equipe entregou (fonte para verificação pela banca) |

**Entregáveis oficiais (PDF):** pasta [`entregaveis/em_pdf/`](entregaveis/em_pdf/)

| PDF | Área |
|-----|------|
| Projeto integrador - Eng. Civil.pdf | Civil |
| Relatório Financeiro…pdf | Produção |
| Projeto integrador.pdf | Conceito do laboratório |
| Arquitetura do sistema.pdf | Computação |
| Relatorio_de_Escopo_e_Arquitetura_Funcional.pdf | Computação |
| cronograma-projeto-faculdade.xlsb | Cronograma Excel |

Os arquivos `.md` em `entregaveis/` são **conversões para leitura no GitHub**, não substituem os PDFs.

> Detalhes: [entregaveis/README.md](entregaveis/README.md)

---

## Links úteis

- [Cronograma por área (versão web)](cronograma.md)
- [Equipe integradora](equipe-integrador.md)
- [Documentação técnica do sistema](../sistema/architecture.md)
- [GitHub Pages — panorama integrado](https://jhowsoares.github.io/SmartBuilding_ExpoTech/engenharias.html)
