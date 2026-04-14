# Perfil Municípios Brasileiros

Plataforma de inteligência municipal com dados abertos — um raio-X de cada um dos 5.570 municípios do Brasil.

## O que é

Sistema que consolida dados de 40+ fontes públicas (TSE, IBGE, CGU, Tesouro Nacional, DATASUS, INEP e outras) em uma plataforma unificada, permitindo consultar o perfil completo de qualquer município brasileiro: eleições, emendas parlamentares, investimentos do PAC, finanças públicas, indicadores de saúde, educação, emprego, infraestrutura e mais.

## Stack

| Camada | Tecnologia |
|---|---|
| **Banco de dados** | PostgreSQL 16+ com PostGIS, pg_trgm, unaccent |
| **ETL / Orquestração** | Python + Airflow + dbt |
| **Backend / API** | FastAPI + SQLAlchemy 2.0 (async) |
| **Frontend** | Next.js 14+ (React) + Tailwind + Recharts + Mapbox |
| **Infra** | Docker Compose (local), GitHub Actions (CI/CD) |
| **Gestão** | Notion (wiki + kanban + ADRs) |

## Estrutura do repositório

```
perfil-municipios/
├── .github/              # CI/CD, issue templates, PR templates
├── src/
│   ├── etl/              # Pipelines de extração, transformação e carga
│   │   ├── extractors/   # Um arquivo por fonte de dados
│   │   ├── transformers/  # Lógica de limpeza e padronização
│   │   ├── loaders/      # Carga no PostgreSQL
│   │   └── utils/        # Helpers compartilhados
│   ├── api/              # Backend FastAPI
│   │   ├── routers/      # Endpoints por domínio
│   │   ├── schemas/      # Pydantic models (request/response)
│   │   ├── services/     # Lógica de negócio
│   │   └── core/         # Config, deps, middleware
│   └── frontend/         # Aplicação Next.js (quando iniciar)
├── db/
│   ├── migrations/       # Alembic migrations
│   └── seeds/            # Dados iniciais (regiões, UFs, cargos)
├── dbt/                  # Transformações dbt
│   ├── models/
│   │   ├── staging/      # 1:1 com fontes raw
│   │   ├── intermediate/ # Joins e lógica intermediária
│   │   └── marts/        # Tabelas finais (fato/dimensão)
│   ├── macros/           # SQL reutilizável
│   └── tests/            # Testes de qualidade de dados
├── scripts/              # Scripts utilitários (setup, backup, etc.)
├── tests/                # Testes automatizados
│   ├── etl/
│   ├── api/
│   └── integration/
├── docs/                 # Documentação técnica
│   ├── architecture/
│   ├── adrs/
│   └── specs/
├── data/                 # Dados locais (ignorado pelo git)
│   ├── raw/              # Downloads brutos
│   ├── processed/        # Arquivos processados
│   └── cache/            # Cache de APIs
├── notebooks/            # Jupyter notebooks exploratórios
└── config/               # Arquivos de configuração
```

## Pré-requisitos

- Python 3.11+
- PostgreSQL 16+ com PostGIS
- Docker e Docker Compose (opcional, recomendado)
- Node.js 20+ (para o frontend, quando iniciar)

## Setup rápido

```bash
# 1. Clonar o repositório
git clone https://github.com/luizfernandocastilho/perfil-municipios.git
cd perfil-municipios

# 2. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais do PostgreSQL

# 5. Subir o banco (via Docker)
docker compose up -d db

# 6. Criar schema
psql $DATABASE_URL -f db/schema/01_ddl_postgresql.sql

# 7. Popular dados iniciais
python scripts/seed_initial_data.py

# 8. Rodar primeiro ETL
python -m src.etl.extractors.ibge_localidades
```

## Setup com Docker (alternativo)

```bash
docker compose up -d
# Banco, API e todas as dependências sobem automaticamente
```

## Comandos úteis

```bash
# Rodar testes
pytest tests/ -v

# Rodar linter
ruff check src/ tests/
ruff format src/ tests/

# Rodar API em modo dev
uvicorn src.api.main:app --reload --port 8000

# Rodar dbt
cd dbt && dbt run && dbt test

# Verificar cobertura de testes
pytest tests/ --cov=src --cov-report=html
```

## Fontes de dados

O projeto consome 40+ fontes de dados públicos. Consulte o [Catálogo de Fontes](docs/catalogo_fontes.md) para a lista completa com URLs, formatos e prioridades.

### Fontes prioritárias (Fase 1)

| Fonte | Órgão | O que traz |
|---|---|---|
| API de Localidades | IBGE | Códigos e nomes dos 5.570 municípios |
| Repositório Eleitoral | TSE | Resultados de eleições, candidaturas |
| SICONFI / Finbra | Tesouro | Finanças municipais |
| Portal da Transparência | CGU | Emendas parlamentares |
| Obras.gov.br | Min. Gestão | Investimentos do PAC |

## Decisões de arquitetura

Decisões técnicas são registradas como ADRs (Architecture Decision Records):

- [ADR-001: PostgreSQL + PostGIS](docs/adrs/adr-001-postgresql.md)
- [ADR-002: FastAPI para o backend](docs/adrs/adr-002-fastapi.md)
- [ADR-003: Schema dimensional](docs/adrs/adr-003-star-schema.md)
- [ADR-004: Notion para gestão](docs/adrs/adr-004-notion.md)

## Roadmap

- [x] **Fase 0** — Fundação (schema, repo, ambiente)
- [ ] **Fase 1** — Dados fundacionais (IBGE, TSE, SICONFI)
- [ ] **Fase 2** — Emendas e PAC
- [ ] **Fase 3** — Saúde, educação, emprego
- [ ] **Fase 4** — Infraestrutura, segurança, meio ambiente
- [ ] **Fase 5** — Frontend MVP
- [ ] **Fase 6** — Inteligência (IA, agentes, chatbot)

## Licença

MIT — veja [LICENSE](LICENSE).
