# Regras de Negócio — RN01 a RN10

Implementadas em `backend/app/ml/business_rules.py`. Avaliadas a cada mensagem MQTT via `RuleContext`.

| ID | Regra | Parâmetro | Implementação |
|----|-------|-----------|---------------|
| RN01 | Desligamento por ausência | 15 min | `_rn01_absence_auto_off()` |
| RN02 | Bloqueio com janela aberta | 5 min | `_rn02_window_open_block()` |
| RN03 | Setpoint 23–25°C | faixa conforto | `_rn03_ideal_temperature()` |
| RN04 | Override manual | 30 min | `mark_manual_override()` |
| RN05 | Alerta consumo elevado | > 50 kWh/dia | `_rn05_consumption_alert()` |
| RN06 | Horário comercial | 07h–21h | `_rn06_operating_hours()` |
| RN07 | Retreinamento ML | sob demanda | `predictor.train()` |
| RN08 | Validação de leituras | Temp 5–55°C | `_rn08_validate_sensor()` |
| RN09 | Auditoria | toda ação | `audit_repository.log()` |
| RN10 | Eficiência energética | +0.15 kW/°C > 24°C | `consumption._estimate_kwh()` |

**Ordem de avaliação:** RN08 → RN06 → RN04 → RN01/RN02/RN03+RN10/RN05

## Como a IA usa o histórico

Features do RandomForest:

- Hora do dia (0–23)
- Dia da semana
- Temperatura e umidade médias
- Percentual de ocupação

Treino: `POST /api/v1/predictions/train` (admin). Modelo salvo localmente em `backend/app/ml/models/` (não versionado no Git).
