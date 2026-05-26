# API — Contrato, Testes e Endpoints

**Base URL:** `http://localhost:8000/api/v1`

## Interfaces de documentação

| Interface | URL | Uso |
|-----------|-----|-----|
| Swagger UI | http://localhost:8000/api/docs | Testar requisições reais |
| ReDoc (local) | http://localhost:8000/api/redoc | Referência de schemas |
| ReDoc (GitHub Pages) | https://jhowsoares.github.io/SmartBuilding_ExpoTech/api.html | Apresentação pública |
| OpenAPI YAML | [`docs/openapi.yaml`](./openapi.yaml) | Contrato estruturado |

## Testar via Swagger

1. Abra http://localhost:8000/api/docs
2. `POST /auth/login` → body:
   ```json
   {"email": "admin@smartbuilding.local", "password": "admin123"}
   ```
3. Copie `access_token`
4. **Authorize** (cadeado) → cole o token
5. Execute qualquer rota protegida

## Testar via PowerShell

```powershell
$body = '{"email":"admin@smartbuilding.local","password":"admin123"}'
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $body
$h = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rooms" -Headers $h
```

## Endpoints principais

### Autenticação

| Método | Endpoint | Auth |
|--------|----------|------|
| POST | `/auth/login` | — |
| POST | `/auth/refresh` | — |
| POST | `/auth/logout` | Bearer |

### Sensores

| Método | Endpoint | Auth |
|--------|----------|------|
| GET | `/sensors` | Bearer |
| GET | `/sensors/{id}/data?period=1h` | Bearer |
| GET | `/sensors/{id}/latest` | Bearer |
| POST | `/sensors/data` | Token IoT |

### Dispositivos

| Método | Endpoint | Auth |
|--------|----------|------|
| GET | `/devices` | Bearer |
| POST | `/devices` | Admin |
| PATCH | `/devices/{id}` | Admin |
| DELETE | `/devices/{id}` | Admin |
| POST | `/devices/{id}/control` | Operador+ |

### Salas, alertas, consumo, ML

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/rooms` | Listar salas |
| GET | `/rooms/{id}/commands` | Histórico de comandos |
| GET | `/alerts?active_only=true` | Alertas ativos |
| GET | `/consumption?period=24h` | Consumo kWh |
| GET | `/predictions/24h` | Predição 24h |
| POST | `/predictions/train` | Retreinar ML (admin) |
| GET | `/health` | Status dos subsistemas |

Controle de AC:

```json
POST /devices/{id}/control
{"action": "on"}
{"action": "off"}
{"action": "setpoint", "value": 23.0}
```

## Credenciais padrão

| Usuário | Senha | Papel |
|---------|-------|-------|
| `admin@smartbuilding.local` | `admin123` | Admin |
| `operador@smartbuilding.local` | `op123` | Operador |
| `visualizador@smartbuilding.local` | `view123` | Viewer |

Inseridas pelo `scripts/seed_db.py` na primeira inicialização.
