"""
Popula dados iniciais de referência no banco.
Uso: python scripts/seed_initial_data.py
"""

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://municipios_app:changeme_local@localhost:5432/perfil_municipios",
)

REGIOES = [
    (1, "Norte"),
    (2, "Nordeste"),
    (3, "Sudeste"),
    (4, "Sul"),
    (5, "Centro-Oeste"),
]

UFS = [
    (11, "RO", "Rondônia", 1),
    (12, "AC", "Acre", 1),
    (13, "AM", "Amazonas", 1),
    (14, "RR", "Roraima", 1),
    (15, "PA", "Pará", 1),
    (16, "AP", "Amapá", 1),
    (17, "TO", "Tocantins", 1),
    (21, "MA", "Maranhão", 2),
    (22, "PI", "Piauí", 2),
    (23, "CE", "Ceará", 2),
    (24, "RN", "Rio Grande do Norte", 2),
    (25, "PB", "Paraíba", 2),
    (26, "PE", "Pernambuco", 2),
    (27, "AL", "Alagoas", 2),
    (28, "SE", "Sergipe", 2),
    (29, "BA", "Bahia", 2),
    (31, "MG", "Minas Gerais", 3),
    (32, "ES", "Espírito Santo", 3),
    (33, "RJ", "Rio de Janeiro", 3),
    (35, "SP", "São Paulo", 3),
    (41, "PR", "Paraná", 4),
    (42, "SC", "Santa Catarina", 4),
    (43, "RS", "Rio Grande do Sul", 4),
    (50, "MS", "Mato Grosso do Sul", 5),
    (51, "MT", "Mato Grosso", 5),
    (52, "GO", "Goiás", 5),
    (53, "DF", "Distrito Federal", 5),
]

FONTES = [
    ("G01", "IBGE Cidades", "IBGE", "https://cidades.ibge.gov.br/", "API / JSON", "Anual"),
    ("G02", "SIDRA / Agregados", "IBGE", "https://sidra.ibge.gov.br/", "API REST", "Variável"),
    ("G03", "API de Localidades", "IBGE", "https://servicodados.ibge.gov.br/api/v1/localidades/", "API REST", "Eventual"),
    ("G04", "Censo 2022", "IBGE", "https://censo2022.ibge.gov.br/", "CSV / API", "Decenal"),
    ("G05", "Malhas Territoriais", "IBGE", "https://www.ibge.gov.br/geociencias/malhas-territoriais.html", "GeoJSON", "Eventual"),
    ("E01", "Repositório Eleitoral", "TSE", "https://dadosabertos.tse.jus.br/dataset/", "CSV", "Pós-eleição"),
    ("E03", "CEPESP Data", "FGV/CEPESP", "https://cepesp.io/", "API / CSV", "Pós-eleição"),
    ("P04", "Portal Transparência - Emendas", "CGU", "https://portaldatransparencia.gov.br/emendas", "API / CSV", "Diária"),
    ("I01", "Obras.gov.br", "Min. Gestão", "https://obras.gov.br/", "API / CSV", "Mensal"),
    ("F01", "SICONFI / Finbra", "Tesouro Nacional", "https://siconfi.tesouro.gov.br/", "API / CSV", "Anual"),
]


async def seed():
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        # Regiões
        for codigo, nome in REGIOES:
            await conn.execute(text(
                "INSERT INTO municipios.dim_regiao (codigo_regiao, nome) "
                "VALUES (:codigo, :nome) ON CONFLICT DO NOTHING"
            ), {"codigo": codigo, "nome": nome})

        # UFs
        for codigo, sigla, nome, regiao in UFS:
            await conn.execute(text(
                "INSERT INTO municipios.dim_uf (codigo_uf, sigla, nome, codigo_regiao) "
                "VALUES (:codigo, :sigla, :nome, :regiao) ON CONFLICT DO NOTHING"
            ), {"codigo": codigo, "sigla": sigla, "nome": nome, "regiao": regiao})

        # Fontes
        for codigo, nome, orgao, url, formato, freq in FONTES:
            await conn.execute(text(
                "INSERT INTO municipios.dim_fonte (codigo, nome, orgao, url, formato, frequencia) "
                "VALUES (:codigo, :nome, :orgao, :url, :formato, :freq) ON CONFLICT DO NOTHING"
            ), {"codigo": codigo, "nome": nome, "orgao": orgao, "url": url, "formato": formato, "freq": freq})

    await engine.dispose()
    print("✓ Dados iniciais inseridos: 5 regiões, 27 UFs, 10 fontes, 11 cargos (via DDL)")


if __name__ == "__main__":
    asyncio.run(seed())
