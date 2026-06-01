# Engenharia Civil

A Engenharia Civil garante que a solução tecnológica seja **compatível com a edificação real** e que a apresentação na ExpoTech tenha suporte físico credível (maquete + análise ambiental).

---

## Contexto no projeto

O foco é o **laboratório de elétrica no subsolo** e, de forma ampliada, as **salas de aula** da instituição. A Civil analisa como a construção influencia conforto térmico, consumo energético e viabilidade de instalação de sensores e cabos.

---

## Contribuições principais

### 1. Levantamento das características das salas

Visitas técnicas para registrar:

- Dimensões e ocupação dos ambientes
- Localização dos aparelhos de ar-condicionado
- Incidência solar e ventilação natural
- Condições de paredes, forros e lajes
- Pontos viáveis para sensores e passagem de cabos

### 2. Avaliação da infraestrutura existente

Análise de **viabilidade de instalação** dos dispositivos de automação:

- Passagem de eletrodutos e cabos sem conflito com instalações existentes
- Fixação segura de sensores
- Durabilidade dos equipamentos no ambiente real

### 3. Conforto térmico

Identificação de fatores que afetam a temperatura percebida (infiltrações, vedação, carga térmica). Essas informações orientam **setpoints e regras de automação** no sistema digital.

### 4. Eficiência energética da edificação

Contribuição para reduzir consumo identificando:

- Vazamentos térmicos e condensação (ex.: tubulação sem isolamento)
- Melhorias construtivas complementares (ex.: **manta isolante** em tubulações)
- Oportunidades de reduzir tempo de funcionamento do AC

### 5. Maquete de apresentação

Projeto e construção de **maquete física** para a ExpoTech:

- Materiais: MDF, acrílico ou PVC
- Espaços reservados para fiação (Elétrica) e sensores (Computação)
- QR codes no suporte físico apontando para documentação e dashboard (`tools/qrcode_civil.html`)

---

## Integração com as outras áreas

| Civil entrega | Quem consome |
|---------------|--------------|
| Dimensões e layout das salas | Computação (cadastro `rooms` no banco) |
| Maquete com passagens para cabos | Elétrica (montagem Arduino/sensores) |
| Diagnóstico de condensação/isolamento | Produção (CAPEX de reparo e isolamento) |
| Conforto térmico esperado | Computação (regras RN01–RN10, setpoint ideal) |

---

## Resultados esperados

- Redução de consumo por melhor aproveitamento da climatização
- Ambientes mais confortáveis para ensino
- Infraestrutura preparada para automação predial
- Maquete integrada à demonstração na feira

---

## Integrantes (Eng. Civil)

Kayke Rennan Lima Matos · Nicolas Soares Pires · Renan Soares · Lucca Martins · Bruno Cassiano

---

## Referências técnicas

- ABNT NBR 16401 — Instalações de ar-condicionado
- ABNT NBR 15220 — Desempenho térmico de edificações

---

## Documento original (PDF)

[Projeto integrador — Eng. Civil (PDF)](entregaveis/em_pdf/Projeto%20integrador%20-%20Eng.%20Civil.pdf)

_Texto convertido para revisão no GitHub:_ [entregaveis/civil-projeto-integrador-original.md](entregaveis/civil-projeto-integrador-original.md)
