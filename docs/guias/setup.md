# 🛠️ Guia de Instalação e Execução

Este guia fornece as instruções necessárias para clonar, configurar e executar a aplicação **Smart Building** em ambiente local utilizando Docker Compose.

---

## 📋 Pré-requisitos

| Ferramenta | Versão Mínima | Função |
| :--- | :--- | :--- |
| **Docker Desktop / Engine** | 4.x+ | Orquestração do banco de dados, API, mensageria e frontend |
| **Git** | 2.x+ | Versionamento e clone do repositório |
| **Navegador Web** | Moderno | Acesso ao painel administrativo e documentação Swagger |

---

## 🐳 Arquitetura de Containers (Docker Compose)

Ao executar o ambiente, os seguintes serviços desacoplados serão inicializados automaticamente:

| Serviço | Descrição | Endereço / Porta Local |
| :--- | :--- | :--- |
| **frontend** | Interface Web (React) | [http://localhost:3000](http://localhost:3000) |
| **backend** | REST API (FastAPI) | [http://localhost:8000](http://localhost:8000) |
| **postgres** | Banco de dados relacional | `localhost:5432` (interno) |
| **redis** | Cache e invalidação de tokens JWT | `localhost:6379` (interno) |
| **mqtt** | Broker de mensageria IoT (Mosquitto) | `localhost:1883` |
| **simulator** | Simulador de telemetria predial (14 salas) | Interno |
| **ngrok** | Túnel HTTP/MQTT para integração com hardware remoto (opcional) | [http://localhost:4040](http://localhost:4040) |

---

## 🚀 Passo a Passo para Execução

### 1. Clonar o Repositório
```bash
git clone [https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git](https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git)
cd SmartBuilding_ExpoTech

```

### 2. Configurar Variáveis de Ambiente (Opcional)

Se for utilizar tunelamento externo para microcontroladores físicos via Ngrok, crie o arquivo `.env` na raiz do projeto:

```env
NGROK_AUTHTOKEN=seu_token_aqui

```

*(Caso esteja testando apenas via simulador local, este passo pode ser ignorado).*

### 3. Inicializar os Serviços

```bash
docker compose up -d --build

```

Acompanhe o status de integridade dos containers:

```bash
docker compose ps

```

### 4. Verificar o Status da API Backend

```bash
docker compose logs backend --tail=30

```

Confirme o status no endpoint de verificação: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health).

### 5. Acesso ao Dashboard e Credenciais Padrão

Navegue até [http://localhost:3000](http://localhost:3000) e utilize uma das credenciais abaixo:

| Papel | E-mail | Senha |
| --- | --- | --- |
| **Administrador** | `admin@smartbuilding.local` | `admin123` |
| **Operador** | `operador@smartbuilding.local` | `op123` |
| **Visualizador** | `visualizador@smartbuilding.local` | `view123` |

---

## 🔧 Comandos Frequentes de Manutenção

* **Visualizar logs em tempo real:**
```bash
docker compose logs -f backend

```


* **Reiniciar um serviço específico:**
```bash
docker compose restart backend

```


* **Recompilar a aplicação frontend:**
```bash
docker compose build frontend && docker compose up -d --no-deps frontend

```


* **Encerrar a aplicação mantendo os dados salvos:**
```bash
docker compose down

```
