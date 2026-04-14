"""
ETL: IBGE Localidades → dim_municipio
Fonte: G03 — API de Localidades do IBGE
Endpoint: https://servicodados.ibge.gov.br/api/v1/localidades/municipios

Popula a tabela dim_municipio com os 5.570 municípios brasileiros,
incluindo hierarquia territorial completa (região, UF, mesorregião,
microrregião, região imediata, região intermediária).

Uso:
    python -m src.etl.extractors.ibge_localidades
    python -m src.etl.extractors.ibge_localidades --extract-only
"""

import asyncio
import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import httpx
from loguru import logger
from unidecode import unidecode

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.etl.base import BaseETL

CAPITAIS = {
    "1100205", "1200401", "1302603", "1400100", "1501402", "1600303",
    "1721000", "2111300", "2211001", "2304400", "2408102", "2507507",
    "2611606", "2704302", "2800308", "2927408", "3106200", "3205309",
    "3304557", "3550308", "4106902", "4205407", "4314902", "5002704",
    "5103403", "5208707", "5300108",
}


def _extract_fields(item: dict) -> dict:
    """
    Extrai campos do município independente do formato da API.
    Suporta tanto o formato aninhado (padrão) quanto o nivelado (view=nivelado).
    """
    # Formato ANINHADO (padrão da API sem view=nivelado):
    # {
    #   "id": 3106200, "nome": "Belo Horizonte",
    #   "microrregiao": {"id": 31030, "nome": "...",
    #     "mesorregiao": {"id": 3107, "nome": "...",
    #       "UF": {"id": 31, "sigla": "MG", "nome": "...",
    #         "regiao": {"id": 3, "sigla": "SE", "nome": "..."}
    #       }
    #     }
    #   },
    #   "regiao-imediata": {"id": 310001, "nome": "...",
    #     "regiao-intermediaria": {"id": 3101, "nome": "...", "UF": {...}}
    #   }
    # }
    #
    # Formato NIVELADO (view=nivelado):
    # {
    #   "id": 3106200, "nome": "Belo Horizonte",
    #   "microrregiao-id": 31030, "microrregiao-nome": "...",
    #   "mesorregiao-id": 3107, "mesorregiao-nome": "...",
    #   "UF-id": 31, "UF-sigla": "MG", "UF-nome": "...",
    #   "regiao-imediata-id": 310001, "regiao-imediata-nome": "...",
    #   "regiao-intermediaria-id": 3101, "regiao-intermediaria-nome": "..."
    # }

    codigo_ibge = str(item["id"]).zfill(7)
    nome = item["nome"].strip()

    # Fallback: deduzir codigo_uf dos 2 primeiros dígitos do código IBGE
    uf_fallback = int(codigo_ibge[:2])

    # Detectar formato: se "microrregiao" é dict, é aninhado
    micro = item.get("microrregiao")

    if isinstance(micro, dict):
        # FORMATO ANINHADO
        meso = micro.get("mesorregiao", {})
        uf_obj = meso.get("UF", {})
        regiao_im = item.get("regiao-imediata", {}) or {}
        regiao_inter = regiao_im.get("regiao-intermediaria", {}) or {}

        return {
            "codigo_ibge": codigo_ibge,
            "nome": nome,
            "nome_normalizado": unidecode(nome).lower().strip(),
            "codigo_uf": uf_obj.get("id") or uf_fallback,
            "codigo_mesorregiao": meso.get("id"),
            "nome_mesorregiao": meso.get("nome"),
            "codigo_microrregiao": micro.get("id"),
            "nome_microrregiao": micro.get("nome"),
            "codigo_regiao_imediata": regiao_im.get("id"),
            "nome_regiao_imediata": regiao_im.get("nome"),
            "codigo_regiao_intermediaria": regiao_inter.get("id"),
            "nome_regiao_intermediaria": regiao_inter.get("nome"),
            "capital": codigo_ibge in CAPITAIS,
        }
    else:
        # FORMATO NIVELADO (view=nivelado)
        return {
            "codigo_ibge": codigo_ibge,
            "nome": nome,
            "nome_normalizado": unidecode(nome).lower().strip(),
            "codigo_uf": item.get("UF-id") or uf_fallback,
            "codigo_mesorregiao": item.get("mesorregiao-id"),
            "nome_mesorregiao": item.get("mesorregiao-nome"),
            "codigo_microrregiao": item.get("microrregiao-id"),
            "nome_microrregiao": item.get("microrregiao-nome"),
            "codigo_regiao_imediata": item.get("regiao-imediata-id"),
            "nome_regiao_imediata": item.get("regiao-imediata-nome"),
            "codigo_regiao_intermediaria": item.get("regiao-intermediaria-id"),
            "nome_regiao_intermediaria": item.get("regiao-intermediaria-nome"),
            "capital": codigo_ibge in CAPITAIS,
        }


class IBGELocalidadesETL(BaseETL):
    """Extrai todos os municípios da API de Localidades do IBGE."""

    FONTE_ID = "G03"
    FONTE_NOME = "IBGE API de Localidades"
    TABELA_DESTINO = "dim_municipio"
    API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

    def extract(self) -> list[dict]:
        logger.info(f"[{self.FONTE_ID}] Chamando API: {self.API_URL}")

        response = httpx.get(self.API_URL, timeout=60, follow_redirects=True)
        response.raise_for_status()
        data = response.json()

        # Log do formato detectado para debug
        if data:
            sample = data[0]
            is_nested = isinstance(sample.get("microrregiao"), dict)
            logger.info(
                f"[{self.FONTE_ID}] Formato detectado: {'aninhado' if is_nested else 'nivelado'}"
            )
            logger.debug(f"[{self.FONTE_ID}] Chaves do primeiro registro: {list(sample.keys())}")

        backup_path = self.raw_dir / f"municipios_{datetime.now().strftime('%Y%m%d')}.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"[{self.FONTE_ID}] Backup salvo: {backup_path}")

        return data

    def transform(self, raw_data: list[dict]) -> list[dict]:
        transformed = []
        errors = 0

        for item in raw_data:
            try:
                registro = _extract_fields(item)
                transformed.append(registro)
            except Exception as e:
                errors += 1
                if errors <= 3:
                    logger.warning(
                        f"[{self.FONTE_ID}] Erro ao transformar item {item.get('id', '?')}: {e} "
                        f"| Chaves: {list(item.keys())}"
                    )

        self._stats["registros_erros"] = errors

        ufs_encontradas = len({r["codigo_uf"] for r in transformed if r["codigo_uf"]})
        capitais_encontradas = sum(1 for r in transformed if r["capital"])

        logger.info(
            f"[{self.FONTE_ID}] Transformação: {len(transformed)} municípios, "
            f"{ufs_encontradas} UFs, {capitais_encontradas} capitais, {errors} erros"
        )

        if len(transformed) < 5500:
            logger.warning(
                f"[{self.FONTE_ID}] ATENÇÃO: apenas {len(transformed)} municípios "
                f"(esperados ~5.570)."
            )

        return transformed

    def load(self, data: list[dict]) -> dict[str, int]:
        return asyncio.run(self._async_load(data))

    async def _async_load(self, data: list[dict]) -> dict[str, int]:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://municipios_app:changeme_local@localhost:5432/perfil_municipios",
        )

        engine = create_async_engine(database_url)
        inseridos = 0
        atualizados = 0

        async with engine.begin() as conn:
            for registro in data:
                result = await conn.execute(
                    text("""
                        INSERT INTO municipios.dim_municipio (
                            codigo_ibge, nome, nome_normalizado, codigo_uf,
                            codigo_mesorregiao, nome_mesorregiao,
                            codigo_microrregiao, nome_microrregiao,
                            codigo_regiao_imediata, nome_regiao_imediata,
                            codigo_regiao_intermediaria, nome_regiao_intermediaria,
                            capital
                        ) VALUES (
                            :codigo_ibge, :nome, :nome_normalizado, :codigo_uf,
                            :codigo_mesorregiao, :nome_mesorregiao,
                            :codigo_microrregiao, :nome_microrregiao,
                            :codigo_regiao_imediata, :nome_regiao_imediata,
                            :codigo_regiao_intermediaria, :nome_regiao_intermediaria,
                            :capital
                        )
                        ON CONFLICT (codigo_ibge) DO UPDATE SET
                            nome = EXCLUDED.nome,
                            nome_normalizado = EXCLUDED.nome_normalizado,
                            codigo_uf = EXCLUDED.codigo_uf,
                            codigo_mesorregiao = EXCLUDED.codigo_mesorregiao,
                            nome_mesorregiao = EXCLUDED.nome_mesorregiao,
                            codigo_microrregiao = EXCLUDED.codigo_microrregiao,
                            nome_microrregiao = EXCLUDED.nome_microrregiao,
                            codigo_regiao_imediata = EXCLUDED.codigo_regiao_imediata,
                            nome_regiao_imediata = EXCLUDED.nome_regiao_imediata,
                            codigo_regiao_intermediaria = EXCLUDED.codigo_regiao_intermediaria,
                            nome_regiao_intermediaria = EXCLUDED.nome_regiao_intermediaria,
                            capital = EXCLUDED.capital,
                            updated_at = NOW()
                        RETURNING (xmax = 0) AS inserted
                    """),
                    registro,
                )
                row = result.fetchone()
                if row and row[0]:
                    inseridos += 1
                else:
                    atualizados += 1

            await conn.execute(
                text("""
                    INSERT INTO municipios.controle_carga (
                        id_fonte, tabela_destino, data_referencia,
                        registros_brutos, registros_inseridos,
                        registros_atualizados, registros_erros, status
                    ) VALUES (
                        (SELECT id_fonte FROM municipios.dim_fonte WHERE codigo = :fonte_id),
                        :tabela, CURRENT_DATE, :brutos, :inseridos, :atualizados, :erros, 'Sucesso'
                    )
                """),
                {
                    "fonte_id": self.FONTE_ID, "tabela": self.TABELA_DESTINO,
                    "brutos": self._stats["registros_brutos"],
                    "inseridos": inseridos, "atualizados": atualizados,
                    "erros": self._stats["registros_erros"],
                },
            )

        await engine.dispose()
        return {"inseridos": inseridos, "atualizados": atualizados}


def run_extract_only():
    etl = IBGELocalidadesETL()
    raw = etl.extract()
    transformed = etl.transform(raw)

    if not transformed:
        logger.error(f"[G03] Nenhum município transformado! Verifique o JSON em {etl.raw_dir}")
        return []

    csv_path = etl.processed_dir / f"dim_municipio_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=transformed[0].keys())
        writer.writeheader()
        writer.writerows(transformed)

    logger.success(f"[G03] CSV salvo: {csv_path} ({len(transformed)} registros)")

    ufs = Counter(r["codigo_uf"] for r in transformed if r["codigo_uf"])
    logger.info(f"[G03] Municípios por UF: {dict(sorted(ufs.items()))}")

    return transformed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ETL: IBGE Localidades → dim_municipio")
    parser.add_argument("--extract-only", action="store_true", help="Apenas extrai e salva CSV")
    args = parser.parse_args()

    if args.extract_only:
        run_extract_only()
    else:
        etl = IBGELocalidadesETL()
        stats = etl.run()
        print(f"\n✓ ETL concluído: {json.dumps(stats, indent=2, default=str)}")
