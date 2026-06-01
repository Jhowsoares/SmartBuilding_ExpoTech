# Tamanho do Repositório — Por que parece pesado?

## Resumo rápido

| O quê | Tamanho típico | Está no Git? |
|-------|----------------|--------------|
| Código-fonte (clone Git) | ~50–100 MB | Sim |
| Modelos ML (`.pkl`) | ~50 MB cada | **Não deve estar** — agora no `.gitignore` |
| Imagens Docker (após `docker compose up`) | **2–8 GB** | Não — ficam no Docker Desktop |
| Volumes do banco (`postgres_data/`) | Cresce com uso | Não — `.gitignore` |

---

## Limpar o histórico Git (remover `.pkl` de commits antigos)

Os commits antigos ainda contêm versões do `consumption_model.pkl` (~7 MB e ~51 MB). Para um clone **menor de verdade**, alguém com acesso de admin ao repositório deve reescrever o histórico **uma vez**:

### Pré-requisitos

```bash
pip install git-filter-repo
```

### Comandos (execute na raiz do projeto)

```bash
# Backup de segurança
git clone --mirror https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git SmartBuilding-backup.git

# Remover todos os .pkl do histórico
git filter-repo --path-glob '*.pkl' --invert-paths --force

# Enviar histórico limpo (ATENÇÃO: reescreve o remoto)
git push origin --force --all
git push origin --force --tags
```

**Aviso:** todos os integrantes precisarão fazer um **clone novo** ou `git fetch --all && git reset --hard origin/main` após o force push.

Alternativa sem force push: criar um repositório novo e migrar — mais seguro para equipes grandes.

---

## Reduzir espaço no disco local (sem mexer no Git)

### Limpar imagens Docker não usadas

```bash
docker system prune -a
```

Isso remove imagens paradas. Na próxima vez que rodar `docker compose up --build`, as imagens serão baixadas de novo.

### Ver o que ocupa espaço no Docker

Docker Desktop → **Settings** → **Resources** → ou:

```bash
docker system df
```

---

## Modelo ML após clone limpo

Sem os `.pkl` no repositório, o backend:

1. Inicia com **modelo sintético** (predições estimadas).
2. Treina um modelo real via `POST /api/v1/predictions/train` (admin) quando houver dados no PostgreSQL.
3. Salva `consumption_model.pkl` e `scaler.pkl` **localmente** em `backend/app/ml/models/` (ignorados pelo Git).
