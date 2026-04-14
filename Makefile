.PHONY: help setup db api test lint format etl-ibge clean

help: ## Mostra este help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ────────────────────────────────────────────────────────────────

setup: ## Setup completo do ambiente local
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt
	cp -n .env.example .env || true
	@echo "\n✓ Ambiente pronto. Ative com: source .venv/bin/activate"

# ─── Banco ────────────────────────────────────────────────────────────────

db: ## Sobe PostgreSQL via Docker
	docker compose up -d db
	@echo "Aguardando banco..."
	@sleep 3
	@echo "✓ PostgreSQL rodando em localhost:5432"

db-schema: ## Executa DDL do schema dimensional
	docker compose exec db psql -U $${POSTGRES_USER:-municipios_app} -d $${POSTGRES_DB:-perfil_municipios} -f /docker-entrypoint-initdb.d/01_ddl_postgresql.sql

db-reset: ## Dropa e recria o schema (CUIDADO!)
	docker compose exec db psql -U $${POSTGRES_USER:-municipios_app} -d $${POSTGRES_DB:-perfil_municipios} -c "DROP SCHEMA IF EXISTS municipios CASCADE;"
	$(MAKE) db-schema

db-psql: ## Abre psql conectado ao banco
	docker compose exec db psql -U $${POSTGRES_USER:-municipios_app} -d $${POSTGRES_DB:-perfil_municipios}

# ─── API ──────────────────────────────────────────────────────────────────

api: ## Roda API em modo dev (com reload)
	uvicorn src.api.main:app --reload --port 8000

# ─── ETL ──────────────────────────────────────────────────────────────────

etl-ibge: ## Roda ETL do IBGE Localidades (dim_municipio)
	python -m src.etl.extractors.ibge_localidades

# ─── Testes ───────────────────────────────────────────────────────────────

test: ## Roda todos os testes
	pytest tests/ -v

test-cov: ## Roda testes com relatório de cobertura
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "\n✓ Relatório HTML em htmlcov/index.html"

# ─── Qualidade de Código ─────────────────────────────────────────────────

lint: ## Verifica lint com ruff
	ruff check src/ tests/

format: ## Formata código com ruff
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Verifica tipos com mypy
	mypy src/ --ignore-missing-imports

check: lint typecheck test ## Lint + typecheck + testes (roda tudo)

# ─── dbt ──────────────────────────────────────────────────────────────────

dbt-run: ## Executa modelos dbt
	cd dbt && dbt run

dbt-test: ## Roda testes dbt
	cd dbt && dbt test

# ─── Docker ───────────────────────────────────────────────────────────────

up: ## Sobe todos os serviços
	docker compose up -d

down: ## Para todos os serviços
	docker compose down

logs: ## Mostra logs dos serviços
	docker compose logs -f

# ─── Limpeza ──────────────────────────────────────────────────────────────

clean: ## Remove caches e arquivos temporários
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "✓ Limpo"
