# 🔌 REST API — Especificação de Contratos e Endpoints

> **Base URL:** `http://localhost:8000/api/v1`

A API REST do **Smart Building** fornece endpoints para autenticação JWT, ingestão de dados de sensores IoT, gerenciamento de dispositivos actuares, controle de salas, telemetria em tempo real e retreinamento de modelos de Machine Learning.

---

## 📑 Interfaces de Documentação Dinâmica

| Interface | URL Local / Remota | Descrição / Aplicação |
| :--- | :--- | :--- |
| **Swagger UI** | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | Testes interativos de requisições e schemas |
| **ReDoc (Local)** | [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc) | Documentação técnica detalhada dos modelos |
| **ReDoc (Pública)** | [https://jhowsoares.github.io/SmartBuilding_ExpoTech/api.html](https://jhowsoares.github.io/SmartBuilding_ExpoTech/api.html) | Espelho público via GitHub Pages |
| **OpenAPI Spec** | [`docs/openapi.yaml`](../openapi.yaml) | Contrato bruto exportável (OpenAPI 3.0) |

---

## 🔐 Autenticação e Níveis de Acesso (RBAC)

A API utiliza tokens **JWT (Bearer Token)** para autenticação e revogação ativa via Redis.

### Credenciais Padrão (Ambiente de Desenvolvimento)
*As contas abaixo são criadas automaticamente via script de seed (`scripts/seed_db.py`):*

| E-mail | Senha | Papel (Role) | Permissões |
| :--- | :--- | :--- | :--- |
| `admin@smartbuilding.local` | `admin123` | **Admin** | Acesso total, gerenciamento de CRUDs e retreinamento de ML |
| `operador@smartbuilding.local` | `op123` | **Operador** | Leitura de métricas e disparo de comandos nos atuadores |
| `visualizador@smartbuilding.local` | `view123` | **Visualizador** | Acesso somente leitura a dashboards e alertas |

---

## 🧪 Teste Rápido via Terminal (cURL / PowerShell)

```powershell
# 1. Realizar Login e obter o Token Access
$body = '{"email":"admin@smartbuilding.local","password":"admin123"}'
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $body

# 2. Consultar a lista de salas enviando o Header de Autenticação
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rooms" -Headers $headers

```

---

## 🗺️ Mapeamento de Endpoints

### 🔑 1. Autenticação (`/auth`)

| Método | Endpoint | Autenticação | Descrição |
| --- | --- | --- | --- |
| `POST` | `/auth/login` | Isento | Autentica usuário e retorna tokens (Access/Refresh) |
| `POST` | `/auth/refresh` | Refresh Token | Renova o Access Token sem reautenticar |
| `POST` | `/auth/logout` | Bearer Token | Invalida o token atual registrando na Blacklist do Redis |

### 🌡️ 2. Sensores e Telemetria (`/sensors`)

| Método | Endpoint | Autenticação | Descrição |
| --- | --- | --- | --- |
| `GET` | `/sensors` | Bearer | Lista todos os sensores cadastrados |
| `GET` | `/sensors/{id}/latest` | Bearer | Retorna a última leitura enviada por um sensor |
| `GET` | `/sensors/{id}/data?period=1h` | Bearer | Histórico de leituras filtrado por período |
| `POST` | `/sensors/data` | Sensor Token | Endpoint de ingestão direta HTTP para nós IoT |

### 🎛️ 3. Dispositivos e Atuadores (`/devices`)

| Método | Endpoint | Autenticação | Descrição |
| --- | --- | --- | --- |
| `GET` | `/devices` | Bearer | Lista todos os atuadores e seus estados atuais |
| `POST` | `/devices` | Admin | Cadastra um novo dispositivo atuador |
| `PATCH` | `/devices/{id}` | Admin | Atualiza parâmetros de um dispositivo |
| `DELETE` | `/devices/{id}` | Admin | Remove um dispositivo do sistema |
| `POST` | `/devices/{id}/control` | Operador+ | Dispara comando de atuação (Ex: liga/desliga Ar) |

> **Exemplo de Payload de Controle de HVAC (`POST /devices/{id}/control`):**
> ```json
> { "action": "on" }
> { "action": "off" }
> { "action": "setpoint", "value": 23.0 }
> 
> ```
> 
> 

### 🏢 4. Gerenciamento de Salas (`/rooms`)

| Método | Endpoint | Autenticação | Descrição |
| --- | --- | --- | --- |
| `GET` | `/rooms` | Bearer | Lista todas as salas com resumo de ocupação |
| `GET` | `/rooms/{id}` | Bearer | Detalhes da sala, incluindo sensores e atuadores associados |
| `POST` | `/rooms` | Admin | Cadastra uma nova sala |
| `PATCH` | `/rooms/{id}` | Admin | Atualiza meta-informações da sala |
| `DELETE` | `/rooms/{id}` | Admin | Apaga o registro da sala |

### 📈 5. Alertas, Consumo Energético e ML (`/alerts`, `/consumption`, `/predictions`)

| Método | Endpoint | Autenticação | Descrição |
| --- | --- | --- | --- |
| `GET` | `/alerts?active_only=true` | Bearer | Retorna lista de alertas ativos do sistema |
| `GET` | `/consumption?period=24h` | Bearer | Métricas de consumo em kWh e custos acumulados |
| `GET` | `/predictions/24h` | Bearer | Projeção preditiva de consumo para as próximas 24h (ML) |
| `POST` | `/predictions/train` | Admin | Dispara o pipeline de retreinamento do modelo ML |
| `GET` | `/health` | Isento | Verificação de integridade da API, banco de dados e Redis |
