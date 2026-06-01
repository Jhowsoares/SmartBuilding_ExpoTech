# Variáveis de Ambiente

## Raiz do projeto (`.env`)

| Variável | Descrição |
|----------|-----------|
| `NGROK_AUTHTOKEN` | Token Ngrok para túnel ESP32 |

> O `.env` está no `.gitignore` — nunca commite secrets.

## Backend (via `docker-compose.yml`)

| Variável | Padrão dev | Descrição |
|----------|------------|-----------|
| `DATABASE_URL` | `postgresql+asyncpg://...@postgres:5432/expotech_db` | PostgreSQL async |
| `JWT_SECRET` | definido no compose | Segredo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Expiração access token |
| `REDIS_URL` | `redis://redis:6379/0` | Redis |
| `MQTT_BROKER` | `mqtt` | Host Mosquitto |
| `MQTT_PORT` | `1883` | Porta MQTT |
| `CORS_ORIGINS` | `*` | Origens browser (dev) |
| `ENERGIA_TARIFA_KWH_BRL` | `0.75` | Tarifa R$/kWh |
| `SENSOR_SERVICE_TOKEN` | token dev | Ingestão IoT |

## Frontend

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | URL da API no browser |

Definida no `docker-compose.yml` para o container `frontend`.
