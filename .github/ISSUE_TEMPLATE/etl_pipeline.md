---
name: "Novo pipeline ETL"
about: "Criar um novo pipeline de extração de dados"
title: "ETL: [FONTE] → [TABELA_DESTINO]"
labels: ["etl", "dados"]
---

## Fonte de dados

- **ID do catálogo:** (ex: G01, E01, P04)
- **Nome:** 
- **Órgão:** 
- **URL:** 
- **Formato:** (CSV / API REST / Scraping / outro)

## Tabela(s) destino

- [ ] `tabela_1`
- [ ] `tabela_2`

## Escopo

Descreva quais dados serão extraídos e quais transformações são necessárias.

## Dependências

- [ ] `dim_municipio` já populada
- [ ] Outras dependências...

## Checklist de implementação

- [ ] Extractor criado em `src/etl/extractors/`
- [ ] Transformer criado em `src/etl/transformers/`
- [ ] Loader testado com carga no banco
- [ ] Registro em `controle_carga` funcionando
- [ ] Testes unitários
- [ ] Documentação no Notion (DB Pipelines)
- [ ] ADR criada (se decisão técnica relevante)

## Notas técnicas

Limites de API, autenticação necessária, volume estimado, etc.
