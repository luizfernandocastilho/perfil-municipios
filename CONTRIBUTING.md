# Contribuindo

## Branch strategy

```
main          ← produção, sempre estável
  └── develop ← integração, merge de features
       ├── feat/etl-ibge-localidades
       ├── feat/api-municipios-endpoint
       ├── fix/etl-tse-encoding
       └── docs/adr-005-redis-cache
```

### Convenção de nomes

- `feat/` — nova funcionalidade
- `fix/` — correção de bug
- `refactor/` — refatoração sem mudança funcional
- `docs/` — apenas documentação
- `etl/` — novo pipeline de dados (atalho para `feat/etl-...`)

## Commits

Usamos conventional commits:

```
feat(etl): add IBGE localidades extractor
fix(api): handle missing municipio gracefully
docs(adr): add ADR-005 Redis caching strategy
refactor(etl): extract common download logic to base class
test(api): add municipio endpoint tests
```

## Fluxo de trabalho

1. Crie uma branch a partir de `develop`
2. Implemente a mudança
3. Rode `make check` (lint + typecheck + testes)
4. Abra PR para `develop`
5. Após merge, atualize o Notion (mover tarefa, atualizar pipeline)

## Padrões de código

- **Python:** ruff para lint e formatação, mypy para tipos
- **SQL:** uppercase para keywords, snake_case para nomes
- **Commits:** conventional commits em português ou inglês
- **Testes:** pytest, mínimo 60% de cobertura

## ETL: como adicionar uma nova fonte

1. Crie issue usando o template "Novo pipeline ETL"
2. Crie o extractor em `src/etl/extractors/nome_da_fonte.py` herdando de `BaseETL`
3. Implemente `extract()`, `transform()`, `load()`
4. Adicione testes em `tests/etl/test_nome_da_fonte.py`
5. Registre o pipeline no Notion (DB Pipelines)
6. Crie ADR se houver decisão técnica relevante
