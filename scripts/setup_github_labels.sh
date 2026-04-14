#!/usr/bin/env bash
# Script para criar labels padronizadas no repositório GitHub.
# Uso: GITHUB_TOKEN=xxx ./scripts/setup_github_labels.sh OWNER/REPO

REPO=${1:?"Uso: $0 OWNER/REPO"}

create_label() {
  gh label create "$1" --color "$2" --description "$3" --repo "$REPO" --force
}

# Tipo
create_label "etl"           "0E8A16" "Pipeline de extração de dados"
create_label "api"           "1D76DB" "Backend / endpoint"
create_label "frontend"      "F9D0C4" "Interface do usuário"
create_label "infra"         "BFD4F2" "Docker, CI/CD, deploy"
create_label "dados"         "7057FF" "Qualidade, schema, migração"
create_label "docs"          "0075CA" "Documentação"
create_label "bug"           "D73A4A" "Algo não funciona"
create_label "enhancement"   "A2EEEF" "Nova funcionalidade ou melhoria"

# Prioridade
create_label "p-critica"     "B60205" "Prioridade crítica"
create_label "p-alta"        "FF9F1C" "Prioridade alta"
create_label "p-media"       "FBCA04" "Prioridade média"

# Fase
create_label "fase-0"        "EDEDED" "Fase 0: Fundação"
create_label "fase-1"        "D4C5F9" "Fase 1: Dados fundacionais"
create_label "fase-2"        "C2E0C6" "Fase 2: Emendas e PAC"
create_label "fase-3"        "FEF2C0" "Fase 3: Saúde, educação, emprego"
create_label "fase-4"        "F9D0C4" "Fase 4: Infra, segurança, ambiente"

# Status
create_label "blocked"       "B60205" "Bloqueado por dependência"
create_label "help-wanted"   "008672" "Precisa de ajuda"
create_label "good-first-issue" "7057FF" "Bom para começar"

echo "Labels criadas com sucesso em $REPO"
