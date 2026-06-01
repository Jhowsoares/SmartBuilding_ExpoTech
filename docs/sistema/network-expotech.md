# Rede e ExpoTech — Ngrok

## Filosofia: 100% local

Todo o ecossistema roda no notebook via Docker:

```
PostgreSQL :5432  │  Redis :6379  │  Mosquitto :1883
FastAPI :8000     │  React :3000
```

Vantagens na feira: sem dependência de nuvem, latência mínima, custo zero, funciona com Wi-Fi instável.

## Conectar ESP32 físico via Ngrok

O ESP32 não alcança `localhost` do notebook. Solução: **túnel TCP Ngrok**.

```
ESP32 → tcp://0.tcp.sa.ngrok.io:XXXXX → Notebook :1883 Mosquitto
```

### Passos

1. Conta em [ngrok.com](https://ngrok.com) → copie o authtoken.
2. Crie `.env` na raiz:
   ```env
   NGROK_AUTHTOKEN=seu_token_aqui
   ```
3. `docker compose up -d`
4. URL do túnel:
   ```bash
   docker compose logs ngrok
   ```
   Ou acesse http://localhost:4040
5. No firmware ESP32:
   ```cpp
   const char* mqtt_server = "0.tcp.sa.ngrok.io";
   const int   mqtt_port   = 15672;  // porta gerada pelo ngrok
   ```

## Descobrir IP local (mesma rede Wi-Fi)

Se ESP32 e notebook estão na **mesma rede**, use o IP do notebook (sem Ngrok):

```powershell
ipconfig   # Windows — IPv4 da Wi-Fi
```

Configure `MQTT_BROKER` no firmware com esse IP e porta `1883`.
