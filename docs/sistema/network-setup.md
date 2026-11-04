# 🌐 Conectividade e Tunelamento IoT (Ngrok)

Este documento orienta sobre a arquitetura de rede local do ecossistema e o procedimento para conectar microcontroladores físicos externos ao ambiente de desenvolvimento.

---

## 🏗️ Filosofia: Ambiente Local Isolado

Todo o ecossistema backend e de mensageria roda isolado em containers na máquina de desenvolvimento:
* **PostgreSQL:** `5432`
* **Redis:** `6379`
* **Mosquitto (MQTT):** `1883`
* **FastAPI:** `8000`
* **React Frontend:** `3000`

**Vantagens:** Ausência de dependência de nuvem durante o desenvolvimento, latência mínima e resiliência a instabilidades de rede.

---

## 🔌 Conexão de Nós Físicos Remotos via Ngrok

Como microcontroladores na borda (ESP32) não alcançam o `localhost` da máquina diretamente quando estão em redes externas, utiliza-se um túnel TCP via Ngrok para o broker MQTT.

### Passo a Passo de Configuração:
1. Obtenha seu `authtoken` em [ngrok.com](https://ngrok.com).
2. Crie um arquivo `.env` na raiz do projeto com a chave:
   ```env
   NGROK_AUTHTOKEN=seu_token_aqui

```

3. Suba o ambiente incluindo o serviço de túnel:
```bash
docker compose up -d

```


4. Obtenha a URL pública TCP gerada pelo Ngrok consultando os logs ou acessando [http://localhost:4040](http://localhost:4040):
* *Exemplo de saída:* `tcp://0.tcp.sa.ngrok.io:15672`


5. No firmware do ESP32, aponte o broker para o endereço e porta gerados:
```cpp
const char* mqtt_server = "0.tcp.sa.ngrok.io";
const int mqtt_port = 15672; // Porta mapeada pelo Ngrok

```



---

## 🏠 Conexão via Rede Local (Mesma Sub-rede Wi-Fi)

Caso o ESP32 e a máquina de desenvolvimento estejam conectados na **mesma rede Wi-Fi**, o uso do Ngrok é dispensable.

1. Descubra o IP local da máquina (`ipconfig` no Windows).
2. Configure o firmware utilizando diretamente o IP local da máquina e a porta padrão `1883`.

