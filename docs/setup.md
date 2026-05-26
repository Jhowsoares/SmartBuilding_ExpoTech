# Configuração e Primeiro Uso

Guia para quem está baixando o projeto pela primeira vez e **não tem experiência com Docker**.

---

## O que você precisa instalar

| Software | Versão mínima | Para quê |
|----------|---------------|----------|
| **Docker Desktop** | 4.x | Sobe banco, API, frontend e simulador com um comando |
| **Git** | qualquer recente | Clonar o repositório |
| **Navegador** | Chrome, Edge ou Firefox | Acessar o dashboard |

> **Windows:** instale o [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/). Durante a instalação, aceite usar WSL 2 se o instalador pedir — é o modo recomendado.
>
> **Mac:** [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/).
>
> **Linux:** [Docker Engine](https://docs.docker.com/engine/install/) + plugin Compose.

### Como saber se o Docker está funcionando

Abra o **Terminal** (PowerShell no Windows) e rode:

```bash
docker --version
docker compose version
```

Se aparecerem números de versão (ex.: `Docker version 27.x`), está pronto.

Abra o **Docker Desktop** e aguarde o ícone da baleia ficar verde/estável antes de continuar.

---

## O que o Docker faz neste projeto (em linguagem simples)

Você **não precisa** instalar Python, Node.js, PostgreSQL ou MQTT manualmente.

O arquivo `docker-compose.yml` na raiz define **vários serviços** (mini-programas) que sobem juntos:

| Serviço | O que é | Porta no seu PC |
|---------|---------|-----------------|
| `frontend` | Interface web (React) | http://localhost:3000 |
| `backend` | API do sistema (FastAPI) | http://localhost:8000 |
| `postgres` | Banco de dados | 5432 (interno) |
| `redis` | Cache e logout JWT | 6379 (interno) |
| `mqtt` | Broker dos sensores IoT | 1883 |
| `simulator` | Simula 14 salas enviando dados | — |
| `ngrok` | Túnel para ESP32 na feira (opcional) | http://localhost:4040 |

O comando `docker compose up` **baixa imagens**, **cria containers** e **conecta tudo numa rede interna**. Na primeira vez pode demorar **5–15 minutos** (download de imagens).

---

## Passo a passo — primeira execução

### 1. Clone o repositório

```bash
git clone https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git
cd SmartBuilding_ExpoTech
```

### 2. (Opcional) Configure o Ngrok — só se for usar ESP32 físico na feira

Crie um arquivo `.env` na **raiz** do projeto (copie do exemplo abaixo):

```env
NGROK_AUTHTOKEN=seu_token_aqui
```

Obtenha o token em [ngrok.com/dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).  
Se você **só vai testar no notebook**, pode pular este passo.

### 3. Suba o sistema

Na pasta do projeto:

```bash
docker compose up -d --build
```

| Flag | Significado |
|------|-------------|
| `up` | Inicia os serviços |
| `-d` | Roda em segundo plano (terminal fica livre) |
| `--build` | Recompila frontend/backend se o código mudou |

**Aguarde** até todos os containers ficarem saudáveis. Acompanhe com:

```bash
docker compose ps
```

Todos devem mostrar `running` ou `healthy`.

### 4. Confirme que a API subiu

```bash
docker compose logs backend --tail=30
```

Procure a linha: **`Application startup complete.`**

Teste no navegador: http://localhost:8000/api/v1/health  
Deve retornar JSON com `"status": "ok"`.

### 5. Acesse o dashboard

1. Abra http://localhost:3000
2. Faça login:

| Email | Senha | Papel |
|-------|-------|-------|
| `admin@smartbuilding.local` | `admin123` | Admin |
| `operador@smartbuilding.local` | `op123` | Operador |
| `visualizador@smartbuilding.local` | `view123` | Viewer |

Pronto — o simulador já envia dados de 14 salas automaticamente.

---

## URLs úteis após subir

| O quê | URL |
|-------|-----|
| Dashboard | http://localhost:3000 |
| Swagger (testar API) | http://localhost:8000/api/docs |
| Health check | http://localhost:8000/api/v1/health |
| Documentação pública | https://jhowsoares.github.io/SmartBuilding_ExpoTech/ |
| Painel Ngrok | http://localhost:4040 |

---

## Comandos do dia a dia

```bash
# Ver se tudo está rodando
docker compose ps

# Ver logs em tempo real (Ctrl+C para sair)
docker compose logs -f backend
docker compose logs -f simulator

# Reiniciar só o backend após mudança no código Python
docker compose restart backend

# Rebuild do frontend após mudança na interface
docker compose build frontend
docker compose up -d --no-deps frontend

# Parar tudo (mantém dados do banco)
docker compose down

# Parar e APAGAR dados do banco (cuidado!)
docker compose down -v
```

---

## Problemas comuns

### "Cannot connect to the Docker daemon"

- Abra o **Docker Desktop** e espere iniciar completamente.
- No Windows, reinicie o Docker Desktop se o WSL estiver instável.

### Porta 3000 ou 8000 já em uso

Outro programa está usando a porta. Feche-o ou altere a porta no `docker-compose.yml` (seção `ports`).

### Dashboard em branco ou interface antiga

Rebuild do frontend + limpar cache do navegador:

```bash
docker compose build frontend
docker compose up -d --no-deps frontend
```

No browser: **Ctrl+Shift+R** (hard refresh).

### Login não funciona

Verifique se o backend está saudável:

```bash
docker compose logs backend --tail=50
```

Se o banco estiver vazio, rode o seed:

```bash
docker compose exec backend sh -c "cd /app && python -m scripts.seed_db"
```

### Predições ML sem modelo

Os arquivos `.pkl` **não vêm no Git** (são gerados localmente). O sistema funciona com modelo sintético. Para treinar:

1. Login como admin no Swagger
2. `POST /api/v1/predictions/train`

Ou aguarde dados acumularem no banco e treine pela tela de Predições.

---

## Próximos passos

- [Arquitetura do sistema](./architecture.md)
- [Testar a API](./api.md)
- [Conectar ESP32](./hardware-esp32.md)
- [Reduzir tamanho do clone](./repositorio.md)
