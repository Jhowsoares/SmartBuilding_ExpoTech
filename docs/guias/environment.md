# 🔑 Variáveis de Ambiente

Este documento especifica a relação de variáveis de ambiente utilizadas pelo ecossistema **Smart Building**.

---

## 📁 Raiz do Projeto (`.env`)

O arquivo `.env` na raiz é utilizado apenas para configurações de infraestrutura externa e deve ser ignorado pelo versionamento.

| Variável | Descrição |
| :--- | :--- |
| `NGROK_AUTHTOKEN` | Token de autenticação para expor portas locais via Ngrok (IoT externo). |

---

## ⚙️ Backend (Configurado via `docker-compose.yml`)

| Variável | Valor Padrão (Dev) | Descrição |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://...@postgres:5432/expotech_db` | Connection string do banco PostgreSQL (Driver Assíncrono). |
| `JWT_SECRET` | Definito no Compose | Chave secreta para assinatura dos tokens JWT. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Tempo de expiração da sessão do usuário. |
| `REDIS_URL` | `redis://redis:6379/0` | Endereço do servidor Redis para cache e gerenciamento de sessões. |
| `MQTT_BROKER` | `mqtt` | Hostname do broker Mosquitto na rede Docker. |
| `MQTT_PORT` | `1883` | Porta de mensageria MQTT. |
| `CORS_ORIGINS` | `*` | Origens permitidas para requisições cross-origin na API. |
| `ENERGIA_TARIFA_KWH_BRL` | `0.75` | Valor base da tarifa de energia elétrica em R$/kWh para cálculo de custos. |
| `SENSOR_SERVICE_TOKEN` | *Token de Autenticação Interno* | Chave de segurança para Ingestão e Validação de Dados de Sensores IoT. |

---

## 🌐 Frontend

| Variável | Valor Padrão | Descrição |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Endpoint base da REST API consumido pela interface web. |

---

