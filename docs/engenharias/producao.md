# Engenharia de Produção

A Engenharia de Produção responde à pergunta: **o projeto faz sentido economicamente?** Analisa custos, retorno, riscos e cronograma de execução.

---

## Contexto no projeto

**Ambiente:** laboratório de elétrica no subsolo (~40–80 m²)  
**Problema:** condensação, umidade e climatização ineficiente  
**Solução:** automação inteligente + isolamento térmico + interface digital (tablet/dashboard)

---

## Análise financeira (resumo)

### Investimento inicial (CAPEX)

Estimativa para implementação real: **R$ 8.200 – R$ 9.000**

Inclui, entre outros:

| Categoria | Exemplos |
|-----------|----------|
| Equipamentos | Sensores, microcontroladores, módulo Bluetooth, tablet |
| Infraestrutura civil | Reparo de vazamento, manta isolante, ajustes na maquete |
| Automação | Eletrodutos aparentes, integração com ar-condicionado |

> A **versão acadêmica** (simulador + Docker + dashboard) opera com **custo zero** de hardware — ideal para desenvolvimento e demonstração na faculdade.

### Custos operacionais (OPEX)

Manutenção preventiva, energia elétrica e calibração periódica dos sensores. Referências: ABNT NBR 15848 (operação e manutenção).

### Economia estimada

Com automação e controle térmico adequado:

| Benefício | Estimativa |
|-----------|------------|
| Redução no uso do AC | **20% a 30%** |
| Menor desgaste de equipamentos | Menos manutenção corretiva |
| Melhoria do ambiente | Menos retrabalho e absenteísmo por desconforto |

### Retorno (ROI e payback)

O retorno vem principalmente de:

1. Economia de energia (kWh × tarifa)
2. Aumento da vida útil dos equipamentos
3. Redução de intervenções emergenciais (vazamento/condensação)

Fórmula de referência:  
`ROI = (Ganho − Investimento) / Investimento`

O payback depende da tarifa local e da redução efetiva de consumo — na simulação do relatório, o retorno é **moderado e viável** para o contexto institucional.

---

## Custos indiretos e riscos

| Item | Observação |
|------|------------|
| Treinamento de usuários | ~R$ 500 (estimado) |
| Tempo de engenharia | Não monetizado (projeto acadêmico) |
| Riscos | Falhas iniciais de calibração, atraso na integração hardware/software |

---

## Cronograma e gestão

A Produção mantém o **cronograma integrado** do projeto (Civil, Computação, Elétrica). Versão web: [cronograma.md](cronograma.md) · Original Excel: [entregaveis/cronograma-projeto-faculdade.xlsb](entregaveis/cronograma-projeto-faculdade.xlsb)

---

## Fluxo de valor (Produção × Computação)

```
Sensores → Backend → Dashboard → Decisão do operador → AC otimizado
                ↓
         Relatórios de consumo (kWh, R$)
                ↓
         Justificativa financeira do investimento
```

O endpoint `/api/v1/consumption` e os relatórios do frontend materializam os dados que a Produção usa para argumentar economia.

---

## Conclusão

- Projeto **viável tecnicamente e financeiramente**
- Versão simulada: custo zero, alta utilidade pedagógica
- Implementação real: investimento moderado com retorno via eficiência energética

---

## Integrantes (Eng. Produção)

Pedro Henrique Teles Viera · Samuel Cavalcante Cardoso

---

## Documento original (PDF)

[Relatório financeiro (PDF)](entregaveis/em_pdf/Relat%C3%B3rio%20Finaceiro%20de%20Implementa%C3%A7%C3%A3o%20de%20Projeto.pdf)

_Texto convertido:_ [entregaveis/producao/relatorio-financeiro.md](entregaveis/producao/relatorio-financeiro.md)
