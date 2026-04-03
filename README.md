# fintech-etl — Coleta de Dados e Orquestração com Airflow

Pipeline de dados financeiros construído com Python, Apache Airflow e Supabase. Extrai dados de ações e criptomoedas via Yahoo Finance, orquestra com Airflow em Docker e carrega no Supabase (PostgreSQL).

## Como rodar
Para salvar o modelo na sua maquina,
instale docker e rode
```bash
docker-compose up
```
Após isso os dados serão salvos e persistidos em data/raw
com isso, voce poderá rodar o modelo e ter as imagens de inferência 
dos resultados obtidos em data/processed.

```bash
uv run src/model/run // ou // python src/model/run
```

Assim, voce tera os dados sendo consultados e salvos de forma diária o modelo 
sendo ajustado todos vez que voce rodar o mmodel. Foi adicionado a DAG do model no 
airflow para rodar todo sábado.

---


## Stack

| Camada | Tecnologia |
|---|---|
| Gerenciamento de dependências | `uv` |
| Extração | `yfinance` |
| Transformação | `pandas` |
| Orquestração | Apache Airflow 2.9 |
| Infraestrutura | Docker Compose |
| Banco de dados | Supabase (PostgreSQL) |
| Migrations | Alembic |
| Linting | Ruff |

---

## Estrutura do projeto

```
fintech-etl/
├── dags/
│   └── fintech_pipeline.py     # DAG principal do Airflow
├── src/
│   ├── extract/
│   │   ├── stocks.py           # Extração de ações via yfinance
│   │   └── crypto.py           # Extração de cripto via yfinance
│   ├── transform/
│   │   └── normalize.py        # Limpeza e padronização
│   └── load/
│       └── supabase.py         # Upsert no Supabase
├── migrations/
│   ├── env.py                  # Configuração do Alembic
│   └── versions/               # Histórico de migrations
├── data/
│   ├── raw/                    # Parquets brutos extraídos
│   └── processed/              # Dados transformados
├── logs/                       # Logs do Airflow
├── plugins/                    # Extensões do Airflow
├── .env                        # Credenciais (nunca commitar)
├── docker-compose.yml          # Ambiente Airflow completo
└── pyproject.toml              # Dependências e configuração
```

---

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose
- [uv](https://astral.sh/uv)
- Conta no [Supabase](https://supabase.com) (gratuita)

---

## Instalação

### 1. Clona o repositório

```bash
git clone https://github.com/seu-usuario/fintech-etl.git
cd fintech-etl
```

### 2. Instala as dependências Python

```bash
uv sync
```

### 3. Configura as variáveis de ambiente

Cria o arquivo `.env` na raiz do projeto:

```bash
DATABASE_URL=postgresql+psycopg2://postgres.xxxx:senha@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
```

A connection string está disponível no painel do Supabase em **Connect → ORMs**.

---

## Banco de dados — Migrations com Alembic

Cria as tabelas no Supabase antes de rodar o pipeline:

```bash
# verifica a conexão
uv run alembic current

# aplica as migrations
uv run alembic upgrade head

# histórico de migrations
uv run alembic history
```

### Schema criado

**`stocks_ohlcv`** — dados OHLCV de ações

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | bigint | Chave primária |
| `ticker` | varchar(20) | Código do ativo (ex: AAPL) |
| `date` | date | Data do pregão |
| `open` | numeric(18,6) | Preço de abertura |
| `high` | numeric(18,6) | Preço máximo |
| `low` | numeric(18,6) | Preço mínimo |
| `close` | numeric(18,6) | Preço de fechamento |
| `volume` | bigint | Volume negociado |
| `created_at` | timestamp | Data de inserção |

**`crypto_ohlcv`** — dados OHLCV de criptomoedas

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | bigint | Chave primária |
| `coin_id` | varchar(50) | ID da moeda (ex: bitcoin) |
| `ticker` | varchar(20) | Par de negociação (ex: BTC-USD) |
| `date` | date | Data |
| `open` | numeric(24,8) | Preço de abertura |
| `high` | numeric(24,8) | Preço máximo |
| `low` | numeric(24,8) | Preço mínimo |
| `close` | numeric(24,8) | Preço de fechamento |
| `volume` | numeric(30,2) | Volume negociado |
| `created_at` | timestamp | Data de inserção |

Ambas as tabelas têm constraints de unicidade e índices por `ticker + date` para otimizar queries por período.

---

## Airflow — Orquestração com Docker

### Subindo o ambiente

```bash
# Linux — define o UID correto (Mac pode pular)
echo -e "AIRFLOW_UID=$(id -u)" >> .env

# inicializa o banco e cria o usuário admin
docker compose up airflow-init

# sobe todos os serviços em background
docker compose up -d

# acompanha os logs do scheduler
docker compose logs -f airflow-scheduler
```

Acessa a UI em **http://localhost:8080** com login `admin` / `admin`.

### Serviços do Docker Compose

| Serviço | Função |
|---|---|
| `postgres` | Banco de metadados do Airflow |
| `airflow-webserver` | Interface web (porta 8080) |
| `airflow-scheduler` | Monitora e dispara as DAGs |
| `airflow-init` | Inicializa o banco e cria o usuário |

### Parando e reiniciando

```bash
# para os containers (mantém os dados)
docker compose down

# reinicia o scheduler após alterar DAGs
docker compose restart airflow-scheduler

# derruba tudo incluindo volumes (cuidado)
docker compose down -v
```

---

## DAG — `fintech_pipeline`

### Fluxo

```
extract_stocks ──► load_stocks ──┐
                                 ├──► check_data
extract_crypto ──► load_crypto ──┘
```

### Tasks

| Task | Descrição |
|---|---|
| `extract_stocks` | Baixa OHLCV dos últimos 90 dias via yfinance e salva em parquet |
| `extract_crypto` | Baixa OHLCV de criptomoedas via yfinance e salva em parquet |
| `load_stocks` | Upsert dos dados de ações no Supabase |
| `load_crypto` | Upsert dos dados de cripto no Supabase |
| `check_data` | Valida os arquivos gerados (shape, nulos, existência) |

### Schedule

```python
schedule = "0 21 * * 1-5"  # dias úteis às 21h UTC (18h BRT)
```

O horário foi escolhido após o fechamento do mercado brasileiro (18h BRT = 21h UTC).

### Ativos monitorados

**Ações**
```python
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "PETR4.SA", "VALE3.SA"]
```

**Criptomoedas**
```python
COINS = {
    "bitcoin":  "BTC-USD",
    "ethereum": "ETH-USD",
    "solana":   "SOL-USD",
    "cardano":  "ADA-USD",
}
```
> **⚠️ Atenção**: Caso queira, pode mudar os tickers e coins dentro de constants.
### XCom — comunicação entre tasks

As tasks de extração retornam o caminho do parquet via XCom. As tasks de load recuperam esse caminho para ler e carregar os dados:

```python
# extração retorna o path
def task_extract_stocks(**context) -> str:
    ...
    return str(output_path)  # enviado via XCom

# load recupera via XCom
def task_load_stocks(**context) -> None:
    ti   = context["ti"]
    path = ti.xcom_pull(task_ids="extract_stocks")
    df   = pd.read_parquet(path)
    load_stocks(df)
```

---

## Upsert — sem duplicatas

O load usa `INSERT ... ON CONFLICT DO NOTHING` para garantir idempotência — rodar a mesma DAG duas vezes no mesmo dia não duplica dados:

```sql
INSERT INTO stocks_ohlcv (ticker, date, open, high, low, close, volume)
SELECT ticker, date, open, high, low, close, volume FROM _tmp_stocks_ohlcv
ON CONFLICT (ticker, date) DO NOTHING
```

---

## Desenvolvimento local

### Rodando a extração manualmente

```bash
# ações
uv run python src/extract/stocks.py

# cripto
uv run python src/extract/crypto.py
```

### Linting

```bash
uv run ruff check src/
uv run ruff format src/
```

---

## Próximos passos

- Arquitetura medalhão no Databricks (Bronze → Silver → Gold)
- Transformações com Apache Spark
