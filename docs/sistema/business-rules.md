# 🧠 Motor de Regras de Negócio e Machine Learning

> **Módulo Backend:** `backend/app/ml/business_rules.py`  
> **Mecanismo:** Avaliação assíncrona orientada a eventos por `RuleContext` a cada mensagem MQTT recebida.

O sistema **Smart Building** utiliza um motor de regras combinado a um modelo preditivo de Machine Learning para garantir eficiência energética, preservação dos equipamentos HVAC e conforto térmico nos ambientes.

---

## 📋 Tabela de Regras (RN01 a RN10)

| ID | Regra de Negócio | Parâmetro / Threshold | Método / Implementação no Backend |
| :--- | :--- | :--- | :--- |
| **RN01** | **Desligamento por Ausência** | 15 min sem detecção de presença | `_rn01_absence_auto_off()` |
| **RN02** | **Bloqueio por Janela Aberta** | Janela aberta por > 5 min | `_rn02_window_open_block()` |
| **RN03** | **Faixa de Conforto Térmico** | Setpoint entre 23°C e 25°C | `_rn03_ideal_temperature()` |
| **RN04** | **Override Manual** | Pausa temporária de automação (30 min) | `mark_manual_override()` |
| **RN05** | **Alerta de Consumo Elevado** | Projeção > 50 kWh/dia por zona | `_rn05_consumption_alert()` |
| **RN06** | **Horário Comercial** | Janela operacional (07:00 – 21:00) | `_rn06_operating_hours()` |
| **RN07** | **Retreinamento do Modelo ML** | Disparo sob demanda via REST API | `predictor.train()` |
| **RN08** | **Sanitization & Validation** | Validação de sensores (Temp: 5°C – 55°C) | `_rn08_validate_sensor()` |
| **RN09** | **Trilha de Auditoria** | Registro imutável de todas as ações | `audit_repository.log()` |
| **RN10** | **Cálculo de Eficiência Energética** | Taxa de +0.15 kW/°C acima de 24°C | `consumption._estimate_kwh()` |

---

## 🔄 Fluxo e Ordem de Avaliação do Pipeline

A execução das regras segue uma hierarquia rigorosa para evitar processamento desnecessário e disparos conflitantes:

```text
[ Entrada de Telemetria (MQTT) ]
               │
               ▼
   1. RN08 (Validação de Outliers / Sensores)
               │
               ▼
   2. RN06 (Verificação de Horário Comercial)
               │
               ▼
   3. RN04 (Checagem de Flag de Override Manual)
               │
               ├─► [Se Override Ativo] ──► Ignora automação e encerra
               │
               ▼
   4. Avaliação Paralela:
       ├─► RN01 (Sensor de Ausência)
       ├─► RN02 (Sensor de Contato de Janela)
       └─► RN03 + RN10 (Ajuste Térmico & Eficiência)
               │
               ▼
   5. RN05 (Verificação de Threshold de Alerta de Consumo)
               │
               ▼
   6. RN09 (Gravação do Log de Auditoria no Banco)

```

---

## 🤖 Modelo Preditivo de Machine Learning (RandomForest)

O módulo de predição projeta a demanda energética das próximas 24 horas utilizando o algoritmo **RandomForestRegressor** da biblioteca `scikit-learn`.

### Features de Entrada (Recursos do Modelo)

* **Tempo:** Hora do dia (`0–23`) e Dia da semana (`0–6`).
* **Telemetria:** Temperatura média e Umidade relativa média acumuladas.
* **Ocupação:** Percentual de salas ocupadas no bloco corporativo.

### Treinamento e Persistência

* **Endpoint de Treino:** `POST /api/v1/predictions/train` *(Requer autenticação como Admin)*.
* **Artefatos Gerados:** Salvos em `backend/app/ml/models/` (`consumption_model.pkl` e `scaler.pkl`).
* **Versionamento:** Os artefatos binários `.pkl` são ignorados pelo Git (`.gitignore`) para manter o repositório leve, sendo gerados dinamicamente no ambiente de execução.