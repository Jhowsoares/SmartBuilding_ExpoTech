# 🧹 Guia de Manutenção e Otimização do Repositório

Este documento estabelece as diretrizes de higiene de código, gerenciamento de artefatos binários e otimização do ambiente Docker para o projeto **Smart Building**.

---

## 📊 Estrutura de Espaço e Artefatos

| Componente | Tamanho Médio | Presente no Git? | Diretriz de Versionamento |
| :--- | :--- | :--- | :--- |
| **Código-fonte** | ~50–100 MB | ✅ Sim | Commits regulares |
| **Modelos ML (`.pkl`)** | ~50 MB cada | ❌ Não | Adicionado ao `.gitignore` (gerado via pipeline) |
| **Imagens Docker** | ~2–8 GB | ❌ Não | Armazenadas localmente no Docker Engine |
| **Volumes PostgreSQL** | Dinâmico | ❌ Não | Gerenciado via volumes nomeados (`.gitignore`) |

---

## 🧼 Higiene do Histórico Git (Remoção de Artefatos Binários)

Modelos de Machine Learning e binários compilados não devem ser versionados diretamente no Git para evitar a inflação do histórico. 

Caso artefatos pesados (como arquivos `.pkl`) tenham sido registrados em commits antigos, utilize a ferramenta `git-filter-repo` para purgar os registros do histórico mantendo o clone leve:

### Pré-requisitos
```bash
pip install git-filter-repo

```

### Procedimento de Purga no Histórico

```bash
# 1. Realizar backup de segurança do repositório (bare clone)
git clone --mirror [https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git](https://github.com/Jhowsoares/SmartBuilding_ExpoTech.git) SmartBuilding-backup.git

# 2. Remover todos os artefatos .pkl do histórico de commits
git filter-repo --path-glob '*.pkl' --invert-paths --force

# 3. Atualizar o repositório remoto (requer privilégios de administração)
git push origin --force --all
git push origin --force --tags

```

> **Nota para a equipe:** Após a reescrita de histórico com `force push`, todos os desenvolvedores devem executar um `git fetch --all && git reset --hard origin/main` ou realizar um novo clone limpo do projeto.

---

## 🐳 Otimização e Limpeza do Ambiente Docker

Durante o desenvolvimento contínuo, o acúmulo de imagens antigas e containers parados pode ocupar espaço considerável no disco.

### Limpeza de Recursos Órfãos

Para remover containers parados, redes não utilizadas e imagens sem tags (dangling images):

```bash
docker system prune -a

```

### Verificação de Consumo de Disco

```bash
docker system df

```

---

## 🤖 Gestão dos Modelos de Machine Learning

Para garantir a portabilidade do repositório sem a necessidade de hospedar arquivos `.pkl` pesados no versionamento:

1. Ao subir a aplicação via Docker, o backend inicia com um **modelo sintético inicial**.
2. O treinamento do modelo preditivo real é disparado via endpoint autenticado: `POST /api/v1/predictions/train`.
3. Os artefatos resultantes (`consumption_model.pkl` e `scaler.pkl`) são salvos localmente no diretório `backend/app/ml/models/` e são ignorados pelo `.gitignore`.