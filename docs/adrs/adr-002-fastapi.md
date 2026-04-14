# ADR-002: FastAPI para o backend

**Status:** Aceita  
**Data:** 2026-04-13  
**Categoria:** Backend

## Contexto

Precisamos de uma API REST performática com documentação automática, que compartilhe o ecossistema Python dos ETLs.

## Decisão

FastAPI com SQLAlchemy 2.0 async e Pydantic v2 para validação.

## Alternativas consideradas

- **Django REST Framework:** Mais pesado, sync por padrão, ORM próprio (não SQLAlchemy).
- **Flask:** Sem async nativo, sem validação automática, sem docs Swagger out-of-the-box.
- **Express.js (Node):** Performático, mas introduz segunda linguagem no projeto.

## Consequências

**Positivas:** Async nativo, tipagem forte com Pydantic, Swagger/OpenAPI automático, mesmo ecossistema dos ETLs.

**Negativas:** Menos "batteries included" que Django (auth, admin). Mitigado com bibliotecas dedicadas quando necessário.
