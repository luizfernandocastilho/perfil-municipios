"""Testes para o ETL IBGE Localidades."""

import pytest
from src.etl.extractors.ibge_localidades import IBGELocalidadesETL, CAPITAIS, _extract_fields


@pytest.fixture
def etl():
    return IBGELocalidadesETL()


@pytest.fixture
def nested_response():
    """Formato aninhado (padrão da API sem view=nivelado)."""
    return [
        {
            "id": 3106200,
            "nome": "Belo Horizonte",
            "microrregiao": {
                "id": 31030,
                "nome": "Belo Horizonte",
                "mesorregiao": {
                    "id": 3107,
                    "nome": "Metropolitana de Belo Horizonte",
                    "UF": {
                        "id": 31,
                        "sigla": "MG",
                        "nome": "Minas Gerais",
                        "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"},
                    },
                },
            },
            "regiao-imediata": {
                "id": 310001,
                "nome": "Belo Horizonte",
                "regiao-intermediaria": {
                    "id": 3101,
                    "nome": "Belo Horizonte",
                    "UF": {"id": 31, "sigla": "MG", "nome": "Minas Gerais",
                           "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"}},
                },
            },
        },
        {
            "id": 3550308,
            "nome": "São Paulo",
            "microrregiao": {
                "id": 35061,
                "nome": "São Paulo",
                "mesorregiao": {
                    "id": 3515,
                    "nome": "Metropolitana de São Paulo",
                    "UF": {
                        "id": 35,
                        "sigla": "SP",
                        "nome": "São Paulo",
                        "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"},
                    },
                },
            },
            "regiao-imediata": {
                "id": 350001,
                "nome": "São Paulo",
                "regiao-intermediaria": {
                    "id": 3501,
                    "nome": "São Paulo",
                    "UF": {"id": 35, "sigla": "SP", "nome": "São Paulo",
                           "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"}},
                },
            },
        },
        {
            "id": 1100015,
            "nome": "Alta Floresta D'Oeste",
            "microrregiao": {
                "id": 11006,
                "nome": "Cacoal",
                "mesorregiao": {
                    "id": 1102,
                    "nome": "Leste Rondoniense",
                    "UF": {
                        "id": 11,
                        "sigla": "RO",
                        "nome": "Rondônia",
                        "regiao": {"id": 1, "sigla": "N", "nome": "Norte"},
                    },
                },
            },
            "regiao-imediata": {
                "id": 110002,
                "nome": "Cacoal",
                "regiao-intermediaria": {
                    "id": 1102,
                    "nome": "Ji-Paraná",
                    "UF": {"id": 11, "sigla": "RO", "nome": "Rondônia",
                           "regiao": {"id": 1, "sigla": "N", "nome": "Norte"}},
                },
            },
        },
    ]


@pytest.fixture
def flat_response():
    """Formato nivelado (view=nivelado)."""
    return [
        {
            "id": 3106200,
            "nome": "Belo Horizonte",
            "microrregiao-id": 31030,
            "microrregiao-nome": "Belo Horizonte",
            "mesorregiao-id": 3107,
            "mesorregiao-nome": "Metropolitana de Belo Horizonte",
            "UF-id": 31, "UF-sigla": "MG", "UF-nome": "Minas Gerais",
            "regiao-id": 3, "regiao-sigla": "SE", "regiao-nome": "Sudeste",
            "regiao-imediata-id": 310001,
            "regiao-imediata-nome": "Belo Horizonte",
            "regiao-intermediaria-id": 3101,
            "regiao-intermediaria-nome": "Belo Horizonte",
        },
    ]


class TestExtractFields:
    def test_nested_format(self, nested_response):
        result = _extract_fields(nested_response[0])
        assert result["codigo_ibge"] == "3106200"
        assert result["nome"] == "Belo Horizonte"
        assert result["codigo_uf"] == 31
        assert result["nome_mesorregiao"] == "Metropolitana de Belo Horizonte"
        assert result["nome_microrregiao"] == "Belo Horizonte"
        assert result["nome_regiao_imediata"] == "Belo Horizonte"
        assert result["nome_regiao_intermediaria"] == "Belo Horizonte"

    def test_flat_format(self, flat_response):
        result = _extract_fields(flat_response[0])
        assert result["codigo_ibge"] == "3106200"
        assert result["codigo_uf"] == 31
        assert result["nome_mesorregiao"] == "Metropolitana de Belo Horizonte"

    def test_both_formats_same_result(self, nested_response, flat_response):
        nested = _extract_fields(nested_response[0])
        flat = _extract_fields(flat_response[0])
        assert nested["codigo_ibge"] == flat["codigo_ibge"]
        assert nested["codigo_uf"] == flat["codigo_uf"]
        assert nested["nome_mesorregiao"] == flat["nome_mesorregiao"]


class TestTransform:
    def test_transform_count(self, etl, nested_response):
        result = etl.transform(nested_response)
        assert len(result) == 3

    def test_codigo_ibge_7_digitos(self, etl, nested_response):
        result = etl.transform(nested_response)
        for r in result:
            assert len(r["codigo_ibge"]) == 7

    def test_nome_normalizado_sem_acentos(self, etl, nested_response):
        result = etl.transform(nested_response)
        sp = next(r for r in result if r["codigo_ibge"] == "3550308")
        assert sp["nome_normalizado"] == "sao paulo"

    def test_nome_normalizado_apostrofo(self, etl, nested_response):
        result = etl.transform(nested_response)
        af = next(r for r in result if r["codigo_ibge"] == "1100015")
        assert "d'oeste" in af["nome_normalizado"]

    def test_capitais_identificadas(self, etl, nested_response):
        result = etl.transform(nested_response)
        bh = next(r for r in result if r["codigo_ibge"] == "3106200")
        sp = next(r for r in result if r["codigo_ibge"] == "3550308")
        af = next(r for r in result if r["codigo_ibge"] == "1100015")
        assert bh["capital"] is True
        assert sp["capital"] is True
        assert af["capital"] is False

    def test_hierarquia_completa(self, etl, nested_response):
        result = etl.transform(nested_response)
        bh = next(r for r in result if r["codigo_ibge"] == "3106200")
        assert bh["codigo_uf"] == 31
        assert bh["codigo_mesorregiao"] == 3107
        assert bh["codigo_microrregiao"] == 31030
        assert bh["codigo_regiao_imediata"] == 310001
        assert bh["codigo_regiao_intermediaria"] == 3101

    def test_transform_empty(self, etl):
        assert etl.transform([]) == []


class TestCapitais:
    def test_total_27(self):
        assert len(CAPITAIS) == 27

    def test_brasilia(self):
        assert "5300108" in CAPITAIS


class TestConfig:
    def test_fonte_id(self, etl):
        assert etl.FONTE_ID == "G03"

    def test_tabela_destino(self, etl):
        assert etl.TABELA_DESTINO == "dim_municipio"

    def test_directories_created(self, etl):
        assert etl.raw_dir.exists()
        assert etl.processed_dir.exists()
