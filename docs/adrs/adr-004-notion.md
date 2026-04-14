# ADR-004: Notion como ferramenta de gestão (solo dev)

**Status:** Aceita  
**Data:** 2026-04-13  
**Categoria:** Gestão

## Contexto

Projeto solo precisa de rastreabilidade sem overhead de ferramentas enterprise. Precisamos de wiki, kanban, catálogo de fontes e registro de decisões técnicas em um só lugar.

## Decisão

Notion para wiki, kanban, catálogo de fontes de dados e ADRs. GitHub Issues/Projects como complemento para tracking de código.

## Alternativas consideradas

- **Jira:** Overkill para dev solo, curva de aprendizado alta, pago para funcionalidades úteis.
- **GitHub Projects:** Bom para issues, mas fraco para documentação, wiki e databases relacionais.
- **Linear:** Excelente UX, mas pago e sem wiki integrada.
- **Obsidian:** Bom para notas pessoais, mas sem kanban nativo e sem databases relacionais.

## Consequências

**Positivas:** Tudo em um lugar, databases relacionais nativos (fontes ↔ pipelines ↔ tarefas), templates flexíveis, acesso web e mobile.

**Negativas:** Sem integração nativa com terminal/CI. Mitigado com links manuais entre Notion e GitHub.
