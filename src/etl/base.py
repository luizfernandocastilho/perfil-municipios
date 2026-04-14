"""
Base class para todos os pipelines ETL.
Cada extrator herda desta classe e implementa extract(), transform(), load().
"""

import hashlib
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


class BaseETL(ABC):
    """Template Method pattern para pipelines ETL."""

    # Sobrescrever na subclasse
    FONTE_ID: str = ""          # Ex: "G01", "E01"
    FONTE_NOME: str = ""        # Ex: "IBGE Localidades"
    TABELA_DESTINO: str = ""    # Ex: "dim_municipio"

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw" / self.FONTE_ID
        self.processed_dir = self.data_dir / "processed" / self.FONTE_ID
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self._stats = {
            "registros_brutos": 0,
            "registros_inseridos": 0,
            "registros_atualizados": 0,
            "registros_erros": 0,
            "inicio": None,
            "fim": None,
        }

    def run(self) -> dict[str, Any]:
        """Executa o pipeline completo: extract → transform → load."""
        logger.info(f"[{self.FONTE_ID}] Iniciando ETL: {self.FONTE_NOME} → {self.TABELA_DESTINO}")
        self._stats["inicio"] = datetime.now()

        try:
            raw_data = self.extract()
            logger.info(f"[{self.FONTE_ID}] Extração concluída: {len(raw_data)} registros brutos")
            self._stats["registros_brutos"] = len(raw_data)

            transformed = self.transform(raw_data)
            logger.info(f"[{self.FONTE_ID}] Transformação concluída: {len(transformed)} registros")

            result = self.load(transformed)
            self._stats["registros_inseridos"] = result.get("inseridos", 0)
            self._stats["registros_atualizados"] = result.get("atualizados", 0)

            self._stats["fim"] = datetime.now()
            duracao = (self._stats["fim"] - self._stats["inicio"]).total_seconds()
            logger.success(
                f"[{self.FONTE_ID}] ETL concluído em {duracao:.1f}s — "
                f"{self._stats['registros_inseridos']} inseridos, "
                f"{self._stats['registros_atualizados']} atualizados, "
                f"{self._stats['registros_erros']} erros"
            )
            return self._stats

        except Exception as e:
            self._stats["fim"] = datetime.now()
            logger.error(f"[{self.FONTE_ID}] ETL falhou: {e}")
            raise

    @abstractmethod
    def extract(self) -> list[dict]:
        """Extrai dados da fonte. Retorna lista de dicts com dados brutos."""
        ...

    @abstractmethod
    def transform(self, raw_data: list[dict]) -> list[dict]:
        """Limpa e transforma os dados. Retorna lista de dicts prontos para carga."""
        ...

    @abstractmethod
    def load(self, data: list[dict]) -> dict[str, int]:
        """Carrega dados no banco. Retorna contagem de inseridos/atualizados."""
        ...

    @staticmethod
    def hash_file(filepath: Path) -> str:
        """Calcula SHA-256 de um arquivo para detectar mudanças."""
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def download_file(self, url: str, filename: str, force: bool = False) -> Path:
        """Baixa arquivo se não existir ou se force=True."""
        import requests
        filepath = self.raw_dir / filename
        if filepath.exists() and not force:
            logger.debug(f"[{self.FONTE_ID}] Arquivo já existe: {filename}")
            return filepath

        logger.info(f"[{self.FONTE_ID}] Baixando {url}")
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"[{self.FONTE_ID}] Salvo em {filepath} ({filepath.stat().st_size / 1024:.0f} KB)")
        return filepath
