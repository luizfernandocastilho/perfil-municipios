"""Fixtures compartilhadas para testes."""

import pytest


@pytest.fixture
def sample_municipio():
    """Dado de teste para um município."""
    return {
        "codigo_ibge": "3106200",
        "nome": "Belo Horizonte",
        "nome_normalizado": "belo horizonte",
        "codigo_uf": 31,
        "capital": True,
        "area_km2": 331.401,
    }


@pytest.fixture
def sample_parlamentar():
    """Dado de teste para um parlamentar."""
    return {
        "nome_completo": "Fulano de Tal",
        "nome_urna": "FULANO",
        "genero": "Masculino",
        "partido_sigla": "PARTIDO",
    }
