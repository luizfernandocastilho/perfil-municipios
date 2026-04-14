# ADR-001: PostgreSQL + PostGIS como banco principal

**Status:** Aceita  
**Data:** 2026-04-13  
**Categoria:** Banco de dados

## Contexto

Precisamos de um banco que suporte simultaneamente dados relacionais (eleições, emendas, finanças), geoespaciais (geometrias de 5.570 municípios para mapas coropléticos), full-text search (busca por nome de município/parlamentar com tolerância a erros), e JSON (respostas de APIs heterogêneas durante ETL).

## Decisão

PostgreSQL 16+ com as extensões PostGIS (geodados), pg_trgm (busca por similaridade) e unaccent (normalização de acentos).

## Alternativas consideradas

- **MySQL:** Sem suporte geoespacial nativo robusto. PostGIS é significativamente mais maduro.
- **MongoDB:** Bom para documentos flexíveis, mas perdemos integridade referencial e JOINs eficientes — críticos para o star schema.
- **DuckDB:** Excelente para analytics, mas sem PostGIS, sem server mode para API concorrente.
- **SQLite + SpatiaLite:** Leve para dev, mas sem concorrência para API em produção.

## Consequências

**Positivas:** Banco maduro e gratuito, comunidade enorme, PostGIS é padrão ouro para geodados, pg_trgm resolve busca fuzzy sem Elasticsearch, JSON nativo para flexibilidade.

**Negativas:** Mais pesado que SQLite para dev local (mitigado com Docker). Requer aprender extensões específicas.
