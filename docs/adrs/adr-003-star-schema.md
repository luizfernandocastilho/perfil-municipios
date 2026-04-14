# ADR-003: Schema dimensional (star schema)

**Status:** Aceita  
**Data:** 2026-04-13  
**Categoria:** Dados

## Contexto

Dados vêm de 40+ fontes com granularidades, formatos e frequências diferentes. Precisamos de um modelo unificado que permita queries simples e adição incremental de novas fontes.

## Decisão

Star schema com `dim_municipio` como dimensão central e tabelas fato por domínio temático (eleições, emendas, finanças, saúde, etc.).

## Alternativas consideradas

- **Schema normalizado (3NF):** Queries ficam complexas demais com muitos JOINs. Difícil para analytics.
- **Data lake puro (Parquet/Delta):** Sem relações explícitas, requer engine separada (Spark/DuckDB).
- **Schema snowflake:** Mais normalizado que star, mas complexidade adicional sem benefício claro neste caso.

## Consequências

**Positivas:** Queries simples com JOINs previsíveis (sempre via `codigo_ibge`), fácil adicionar novas fontes como nova tabela fato, materialized views para consolidação no frontend.

**Negativas:** Alguma redundância controlada (desnormalização). Mitigado com dbt para garantir consistência.
