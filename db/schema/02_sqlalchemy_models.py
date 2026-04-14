"""
PERFIL MUNICÍPIOS BRASILEIROS — SQLAlchemy Models (v1.0.0)
Para uso com FastAPI + SQLAlchemy 2.0+ (async)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Index, Integer,
    Numeric, SmallInteger, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ─── Base ───────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


SCHEMA = "municipios"


# ─── 1. DIMENSÕES ──────────────────────────────────────────────────────────

class DimRegiao(Base):
    __tablename__ = "dim_regiao"
    __table_args__ = {"schema": SCHEMA}

    codigo_regiao: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nome: Mapped[str] = mapped_column(String(20), nullable=False)

    ufs: Mapped[list["DimUF"]] = relationship(back_populates="regiao")


class DimUF(Base):
    __tablename__ = "dim_uf"
    __table_args__ = {"schema": SCHEMA}

    codigo_uf: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    sigla: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    codigo_regiao: Mapped[int] = mapped_column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_regiao.codigo_regiao"), nullable=False)
    geom = Column(Geometry("MultiPolygon", srid=4326))

    regiao: Mapped["DimRegiao"] = relationship(back_populates="ufs")
    municipios: Mapped[list["DimMunicipio"]] = relationship(back_populates="uf")


class DimMunicipio(Base):
    __tablename__ = "dim_municipio"
    __table_args__ = (
        Index("idx_municipio_uf", "codigo_uf"),
        Index("idx_municipio_nome_trgm", "nome_normalizado", postgresql_using="gin",
              postgresql_ops={"nome_normalizado": "gin_trgm_ops"}),
        {"schema": SCHEMA},
    )

    codigo_ibge: Mapped[str] = mapped_column(String(7), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    nome_normalizado: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo_uf: Mapped[int] = mapped_column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_uf.codigo_uf"), nullable=False)
    codigo_mesorregiao: Mapped[Optional[int]] = mapped_column(Integer)
    nome_mesorregiao: Mapped[Optional[str]] = mapped_column(String(120))
    codigo_microrregiao: Mapped[Optional[int]] = mapped_column(Integer)
    nome_microrregiao: Mapped[Optional[str]] = mapped_column(String(120))
    codigo_regiao_imediata: Mapped[Optional[int]] = mapped_column(Integer)
    nome_regiao_imediata: Mapped[Optional[str]] = mapped_column(String(150))
    codigo_regiao_intermediaria: Mapped[Optional[int]] = mapped_column(Integer)
    nome_regiao_intermediaria: Mapped[Optional[str]] = mapped_column(String(150))
    capital: Mapped[bool] = mapped_column(Boolean, default=False)
    area_km2: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3))
    geom = Column(Geometry("MultiPolygon", srid=4326))
    centroide = Column(Geometry("Point", srid=4326))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    uf: Mapped["DimUF"] = relationship(back_populates="municipios")
    votacoes: Mapped[list["FatoVotacao"]] = relationship(back_populates="municipio")
    emendas: Mapped[list["FatoEmenda"]] = relationship(back_populates="municipio")
    obras: Mapped[list["FatoObraPac"]] = relationship(back_populates="municipio")
    financas: Mapped[list["FatoFinancas"]] = relationship(back_populates="municipio")
    demografia: Mapped[list["FatoDemografia"]] = relationship(back_populates="municipio")
    saude: Mapped[list["FatoSaude"]] = relationship(back_populates="municipio")
    educacao: Mapped[list["FatoEducacao"]] = relationship(back_populates="municipio")
    emprego: Mapped[list["FatoEmprego"]] = relationship(back_populates="municipio")
    infraestrutura: Mapped[list["FatoInfraestrutura"]] = relationship(back_populates="municipio")
    seguranca: Mapped[list["FatoSeguranca"]] = relationship(back_populates="municipio")
    gestao: Mapped[list["FatoGestaoMunicipal"]] = relationship(back_populates="municipio")


class DimPartido(Base):
    __tablename__ = "dim_partido"
    __table_args__ = (
        UniqueConstraint("sigla", "vigencia_inicio"),
        Index("idx_partido_sigla", "sigla"),
        Index("idx_partido_numero", "numero"),
        {"schema": SCHEMA},
    )

    id_partido: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(25), nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    numero: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    data_criacao: Mapped[Optional[date]] = mapped_column(Date)
    situacao: Mapped[str] = mapped_column(String(30), default="Ativo")
    vigencia_inicio: Mapped[date] = mapped_column(Date, nullable=False, default="1900-01-01")
    vigencia_fim: Mapped[Optional[date]] = mapped_column(Date)


class DimParlamentar(Base):
    __tablename__ = "dim_parlamentar"
    __table_args__ = (
        Index("idx_parlamentar_cpf", "cpf_hash"),
        Index("idx_parlamentar_nome_trgm", "nome_completo", postgresql_using="gin",
              postgresql_ops={"nome_completo": "gin_trgm_ops"}),
        {"schema": SCHEMA},
    )

    id_parlamentar: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cpf_hash: Mapped[Optional[str]] = mapped_column(String(64))
    titulo_eleitor: Mapped[Optional[str]] = mapped_column(String(20))
    nome_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    nome_urna: Mapped[Optional[str]] = mapped_column(String(100))
    nome_social: Mapped[Optional[str]] = mapped_column(String(200))
    data_nascimento: Mapped[Optional[date]] = mapped_column(Date)
    genero: Mapped[Optional[str]] = mapped_column(String(20))
    raca_cor: Mapped[Optional[str]] = mapped_column(String(30))
    grau_instrucao: Mapped[Optional[str]] = mapped_column(String(50))
    naturalidade_ibge: Mapped[Optional[str]] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    partido_atual_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_partido.id_partido"))
    foto_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    partido_atual: Mapped[Optional["DimPartido"]] = relationship()
    candidaturas: Mapped[list["FatoCandidatura"]] = relationship(back_populates="parlamentar")
    votacoes: Mapped[list["FatoVotacao"]] = relationship(back_populates="parlamentar")
    emendas: Mapped[list["FatoEmenda"]] = relationship(back_populates="parlamentar")
    mandatos: Mapped[list["HistMandato"]] = relationship(back_populates="parlamentar")


class DimCargo(Base):
    __tablename__ = "dim_cargo"
    __table_args__ = {"schema": SCHEMA}

    id_cargo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_tse: Mapped[Optional[int]] = mapped_column(SmallInteger, unique=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    esfera: Mapped[str] = mapped_column(String(20), nullable=False)
    abrangencia: Mapped[str] = mapped_column(String(20), nullable=False)


class DimEleicao(Base):
    __tablename__ = "dim_eleicao"
    __table_args__ = (
        UniqueConstraint("ano", "tipo"),
        {"schema": SCHEMA},
    )

    id_eleicao: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(100))
    data_1turno: Mapped[Optional[date]] = mapped_column(Date)
    data_2turno: Mapped[Optional[date]] = mapped_column(Date)


class DimFuncaoOrcamentaria(Base):
    __tablename__ = "dim_funcao_orcamentaria"
    __table_args__ = {"schema": SCHEMA}

    codigo_funcao: Mapped[str] = mapped_column(String(5), primary_key=True)
    nome_funcao: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo_subfuncao: Mapped[Optional[str]] = mapped_column(String(5))
    nome_subfuncao: Mapped[Optional[str]] = mapped_column(String(100))


class DimFonte(Base):
    __tablename__ = "dim_fonte"
    __table_args__ = {"schema": SCHEMA}

    id_fonte: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    orgao: Mapped[Optional[str]] = mapped_column(String(100))
    url: Mapped[Optional[str]] = mapped_column(Text)
    formato: Mapped[Optional[str]] = mapped_column(String(50))
    frequencia: Mapped[Optional[str]] = mapped_column(String(30))


class DimTempo(Base):
    __tablename__ = "dim_tempo"
    __table_args__ = {"schema": SCHEMA}

    data: Mapped[date] = mapped_column(Date, primary_key=True)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    mes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    trimestre: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    semestre: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    nome_mes: Mapped[str] = mapped_column(String(15), nullable=False)
    ano_mes: Mapped[str] = mapped_column(String(7), nullable=False)


# ─── 2. FATOS ──────────────────────────────────────────────────────────────

class FatoCandidatura(Base):
    __tablename__ = "fato_candidatura"
    __table_args__ = (
        Index("idx_candidatura_eleicao", "id_eleicao"),
        Index("idx_candidatura_municipio", "codigo_ibge"),
        Index("idx_candidatura_parlamentar", "id_parlamentar"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_eleicao: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_eleicao.id_eleicao"), nullable=False)
    id_parlamentar: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_parlamentar.id_parlamentar"), nullable=False)
    id_cargo: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_cargo.id_cargo"), nullable=False)
    id_partido: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_partido.id_partido"), nullable=False)
    numero_candidato: Mapped[Optional[int]] = mapped_column(Integer)
    codigo_ibge: Mapped[Optional[str]] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"))
    codigo_uf: Mapped[Optional[int]] = mapped_column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_uf.codigo_uf"))
    coligacao: Mapped[Optional[str]] = mapped_column(String(300))
    situacao_candidatura: Mapped[Optional[str]] = mapped_column(String(30))
    situacao_turno: Mapped[Optional[str]] = mapped_column(String(30))
    nome_urna: Mapped[Optional[str]] = mapped_column(String(100))
    despesa_campanha: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    bens_declarados: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    parlamentar: Mapped["DimParlamentar"] = relationship(back_populates="candidaturas")
    eleicao: Mapped["DimEleicao"] = relationship()
    cargo: Mapped["DimCargo"] = relationship()
    partido: Mapped["DimPartido"] = relationship()


class FatoVotacao(Base):
    __tablename__ = "fato_votacao"
    __table_args__ = (
        Index("idx_votacao_eleicao_mun", "id_eleicao", "codigo_ibge"),
        Index("idx_votacao_parlamentar", "id_parlamentar"),
        Index("idx_votacao_partido", "id_partido"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_eleicao: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_eleicao.id_eleicao"), nullable=False)
    turno: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    id_cargo: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_cargo.id_cargo"), nullable=False)
    id_parlamentar: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_parlamentar.id_parlamentar"), nullable=False)
    id_partido: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_partido.id_partido"), nullable=False)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    zona_eleitoral: Mapped[Optional[int]] = mapped_column(SmallInteger)
    votos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentual_votos: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    situacao: Mapped[Optional[str]] = mapped_column(String(30))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="votacoes")
    parlamentar: Mapped["DimParlamentar"] = relationship(back_populates="votacoes")
    eleicao: Mapped["DimEleicao"] = relationship()
    cargo: Mapped["DimCargo"] = relationship()
    partido: Mapped["DimPartido"] = relationship()


class FatoEmenda(Base):
    __tablename__ = "fato_emenda"
    __table_args__ = (
        Index("idx_emenda_municipio", "codigo_ibge"),
        Index("idx_emenda_parlamentar", "id_parlamentar"),
        Index("idx_emenda_ano", "ano_loa"),
        Index("idx_emenda_tipo", "tipo_emenda"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ano_loa: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    numero_emenda: Mapped[Optional[str]] = mapped_column(String(30))
    tipo_emenda: Mapped[str] = mapped_column(String(40), nullable=False)
    id_parlamentar: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_parlamentar.id_parlamentar"))
    nome_autor: Mapped[Optional[str]] = mapped_column(String(200))
    codigo_ibge: Mapped[Optional[str]] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"))
    codigo_uf: Mapped[Optional[int]] = mapped_column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_uf.codigo_uf"))
    codigo_funcao: Mapped[Optional[str]] = mapped_column(String(5), ForeignKey(f"{SCHEMA}.dim_funcao_orcamentaria.codigo_funcao"))
    programa: Mapped[Optional[str]] = mapped_column(String(200))
    acao: Mapped[Optional[str]] = mapped_column(String(200))
    valor_empenhado: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    valor_liquidado: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    valor_resto_pagar: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    situacao: Mapped[Optional[str]] = mapped_column(String(50))
    beneficiario_cnpj: Mapped[Optional[str]] = mapped_column(String(20))
    beneficiario_nome: Mapped[Optional[str]] = mapped_column(String(200))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped[Optional["DimMunicipio"]] = relationship(back_populates="emendas")
    parlamentar: Mapped[Optional["DimParlamentar"]] = relationship(back_populates="emendas")


class FatoObraPac(Base):
    __tablename__ = "fato_obra_pac"
    __table_args__ = (
        Index("idx_obra_municipio", "codigo_ibge"),
        Index("idx_obra_status", "status"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_obra_externo: Mapped[Optional[str]] = mapped_column(String(50))
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    nome_obra: Mapped[Optional[str]] = mapped_column(String(500))
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    eixo: Mapped[Optional[str]] = mapped_column(String(80))
    subeixo: Mapped[Optional[str]] = mapped_column(String(120))
    programa: Mapped[Optional[str]] = mapped_column(String(200))
    executor: Mapped[Optional[str]] = mapped_column(String(200))
    valor_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    valor_executado: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pct_execucao_fisica: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pct_execucao_financeira: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    status: Mapped[Optional[str]] = mapped_column(String(40))
    data_inicio: Mapped[Optional[date]] = mapped_column(Date)
    data_previsao_fim: Mapped[Optional[date]] = mapped_column(Date)
    data_conclusao: Mapped[Optional[date]] = mapped_column(Date)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="obras")


class FatoFinancas(Base):
    __tablename__ = "fato_financas"
    __table_args__ = (
        UniqueConstraint("codigo_ibge", "ano"),
        Index("idx_financas_municipio", "codigo_ibge"),
        Index("idx_financas_ano", "ano"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    populacao_ref: Mapped[Optional[int]] = mapped_column(Integer)
    receita_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_corrente: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_tributaria: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_iss: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_iptu: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_itbi: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_transferencias: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_fpm: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_icms: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_fundeb: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    receita_capital: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_corrente: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_pessoal: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_custeio: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_capital: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_investimento: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_saude: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_educacao: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_assistencia: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_urbanismo: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_seguranca: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    despesa_saneamento: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pct_pessoal_rcl: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pct_saude: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pct_educacao: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    superavit_primario: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    divida_consolidada: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    capag: Mapped[Optional[str]] = mapped_column(String(1))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="financas")


class FatoDemografia(Base):
    __tablename__ = "fato_demografia"
    __table_args__ = (
        UniqueConstraint("codigo_ibge", "ano_referencia", "fonte_dado"),
        Index("idx_demografia_municipio", "codigo_ibge"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano_referencia: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fonte_dado: Mapped[Optional[str]] = mapped_column(String(30))
    populacao_total: Mapped[Optional[int]] = mapped_column(Integer)
    populacao_urbana: Mapped[Optional[int]] = mapped_column(Integer)
    populacao_rural: Mapped[Optional[int]] = mapped_column(Integer)
    populacao_masculina: Mapped[Optional[int]] = mapped_column(Integer)
    populacao_feminina: Mapped[Optional[int]] = mapped_column(Integer)
    densidade_demografica: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    taxa_urbanizacao: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pib_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pib_per_capita: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    pib_agropecuaria: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pib_industria: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pib_servicos: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pib_administracao: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    idhm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    idhm_educacao: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    idhm_renda: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    idhm_longevidade: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    gini: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    salario_medio_mensal: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    renda_per_capita: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    pct_pobreza: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pct_extrema_pobreza: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    taxa_ocupacao: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    empregos_formais: Mapped[Optional[int]] = mapped_column(Integer)
    taxa_mortalidade_infantil: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    esperanca_vida: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    taxa_analfabetismo: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="demografia")


class FatoSaude(Base):
    __tablename__ = "fato_saude"
    __table_args__ = (
        UniqueConstraint("codigo_ibge", "ano"),
        Index("idx_saude_municipio", "codigo_ibge"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cobertura_esf: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    cobertura_acs: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    equipes_esf: Mapped[Optional[int]] = mapped_column(Integer)
    total_estabelecimentos: Mapped[Optional[int]] = mapped_column(Integer)
    leitos_sus: Mapped[Optional[int]] = mapped_column(Integer)
    leitos_uti: Mapped[Optional[int]] = mapped_column(Integer)
    internacoes_sus: Mapped[Optional[int]] = mapped_column(Integer)
    obitos_geral: Mapped[Optional[int]] = mapped_column(Integer)
    nascidos_vivos: Mapped[Optional[int]] = mapped_column(Integer)
    mortalidade_infantil: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    cobertura_vacinal: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    repasse_fns_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    repasse_pab: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    repasse_mac: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="saude")


class FatoEducacao(Base):
    __tablename__ = "fato_educacao"
    __table_args__ = (
        UniqueConstraint("codigo_ibge", "ano"),
        Index("idx_educacao_municipio", "codigo_ibge"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_escolas: Mapped[Optional[int]] = mapped_column(Integer)
    escolas_municipais: Mapped[Optional[int]] = mapped_column(Integer)
    escolas_estaduais: Mapped[Optional[int]] = mapped_column(Integer)
    escolas_federais: Mapped[Optional[int]] = mapped_column(Integer)
    escolas_privadas: Mapped[Optional[int]] = mapped_column(Integer)
    matriculas_total: Mapped[Optional[int]] = mapped_column(Integer)
    matriculas_creche: Mapped[Optional[int]] = mapped_column(Integer)
    matriculas_pre_escola: Mapped[Optional[int]] = mapped_column(Integer)
    matriculas_fundamental: Mapped[Optional[int]] = mapped_column(Integer)
    matriculas_medio: Mapped[Optional[int]] = mapped_column(Integer)
    matriculas_eja: Mapped[Optional[int]] = mapped_column(Integer)
    total_docentes: Mapped[Optional[int]] = mapped_column(Integer)
    docentes_superior: Mapped[Optional[int]] = mapped_column(Integer)
    ideb_anos_iniciais: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1))
    ideb_anos_finais: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1))
    taxa_aprovacao: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    taxa_abandono: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    taxa_distorcao_idade: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    repasse_fnde_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    repasse_pnae: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    repasse_pdde: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="educacao")


class FatoEmprego(Base):
    __tablename__ = "fato_emprego"
    __table_args__ = (
        Index("idx_emprego_municipio", "codigo_ibge"),
        Index("idx_emprego_ano_mes", "ano", "mes"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    mes: Mapped[Optional[int]] = mapped_column(SmallInteger)
    fonte_dado: Mapped[Optional[str]] = mapped_column(String(20))
    admissoes: Mapped[Optional[int]] = mapped_column(Integer)
    desligamentos: Mapped[Optional[int]] = mapped_column(Integer)
    saldo_emprego: Mapped[Optional[int]] = mapped_column(Integer)
    estoque_empregos: Mapped[Optional[int]] = mapped_column(Integer)
    massa_salarial: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    salario_medio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    total_estabelecimentos: Mapped[Optional[int]] = mapped_column(Integer)
    familias_cadastro_unico: Mapped[Optional[int]] = mapped_column(Integer)
    beneficiarios_bolsa_familia: Mapped[Optional[int]] = mapped_column(Integer)
    valor_bolsa_familia: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    beneficiarios_bpc: Mapped[Optional[int]] = mapped_column(Integer)
    valor_bpc: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="emprego")


class FatoInfraestrutura(Base):
    __tablename__ = "fato_infraestrutura"
    __table_args__ = (
        UniqueConstraint("codigo_ibge", "ano"),
        Index("idx_infra_municipio", "codigo_ibge"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cobertura_agua: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    cobertura_esgoto: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tratamento_esgoto: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    perdas_agua: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    cobertura_coleta_lixo: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    consumidores_energia: Mapped[Optional[int]] = mapped_column(Integer)
    consumo_energia_mwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    geracao_distribuida_kw: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    acessos_banda_larga: Mapped[Optional[int]] = mapped_column(Integer)
    acessos_movel: Mapped[Optional[int]] = mapped_column(Integer)
    cobertura_4g: Mapped[Optional[bool]] = mapped_column(Boolean)
    cobertura_5g: Mapped[Optional[bool]] = mapped_column(Boolean)
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="infraestrutura")


class FatoSeguranca(Base):
    __tablename__ = "fato_seguranca"
    __table_args__ = (
        Index("idx_seguranca_municipio", "codigo_ibge"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    mes: Mapped[Optional[int]] = mapped_column(SmallInteger)
    homicidios: Mapped[Optional[int]] = mapped_column(Integer)
    latrocinios: Mapped[Optional[int]] = mapped_column(Integer)
    roubos: Mapped[Optional[int]] = mapped_column(Integer)
    furtos: Mapped[Optional[int]] = mapped_column(Integer)
    trafico_drogas: Mapped[Optional[int]] = mapped_column(Integer)
    taxa_homicidios_100k: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="seguranca")


class FatoGestaoMunicipal(Base):
    __tablename__ = "fato_gestao_municipal"
    __table_args__ = (
        UniqueConstraint("codigo_ibge", "ano"),
        Index("idx_gestao_municipio", "codigo_ibge"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"), nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    nome_prefeito: Mapped[Optional[str]] = mapped_column(String(200))
    partido_prefeito: Mapped[Optional[str]] = mapped_column(String(25))
    vice_prefeito: Mapped[Optional[str]] = mapped_column(String(200))
    tem_plano_diretor: Mapped[Optional[bool]] = mapped_column(Boolean)
    tem_conselho_saude: Mapped[Optional[bool]] = mapped_column(Boolean)
    tem_conselho_educacao: Mapped[Optional[bool]] = mapped_column(Boolean)
    tem_conselho_meio_ambiente: Mapped[Optional[bool]] = mapped_column(Boolean)
    tem_guarda_municipal: Mapped[Optional[bool]] = mapped_column(Boolean)
    total_servidores: Mapped[Optional[int]] = mapped_column(Integer)
    servidores_estatutarios: Mapped[Optional[int]] = mapped_column(Integer)
    servidores_comissionados: Mapped[Optional[int]] = mapped_column(Integer)
    total_vereadores: Mapped[Optional[int]] = mapped_column(SmallInteger)
    id_fonte: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"))
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    municipio: Mapped["DimMunicipio"] = relationship(back_populates="gestao")


# ─── 3. TABELAS AUXILIARES ─────────────────────────────────────────────────

class HistFiliacaoPartidaria(Base):
    __tablename__ = "hist_filiacao_partidaria"
    __table_args__ = (
        Index("idx_filiacao_parlamentar", "id_parlamentar"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_parlamentar: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_parlamentar.id_parlamentar"), nullable=False)
    id_partido: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_partido.id_partido"), nullable=False)
    data_filiacao: Mapped[Optional[date]] = mapped_column(Date)
    data_desfiliacao: Mapped[Optional[date]] = mapped_column(Date)
    motivo: Mapped[Optional[str]] = mapped_column(String(100))


class HistMandato(Base):
    __tablename__ = "hist_mandato"
    __table_args__ = (
        Index("idx_mandato_parlamentar", "id_parlamentar"),
        Index("idx_mandato_municipio", "codigo_ibge"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_parlamentar: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_parlamentar.id_parlamentar"), nullable=False)
    id_cargo: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_cargo.id_cargo"), nullable=False)
    id_eleicao: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_eleicao.id_eleicao"), nullable=False)
    codigo_ibge: Mapped[Optional[str]] = mapped_column(String(7), ForeignKey(f"{SCHEMA}.dim_municipio.codigo_ibge"))
    codigo_uf: Mapped[Optional[int]] = mapped_column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_uf.codigo_uf"))
    id_partido: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_partido.id_partido"))
    inicio_mandato: Mapped[Optional[date]] = mapped_column(Date)
    fim_mandato: Mapped[Optional[date]] = mapped_column(Date)
    situacao: Mapped[str] = mapped_column(String(30), default="Exercício")

    parlamentar: Mapped["DimParlamentar"] = relationship(back_populates="mandatos")


class ControleCarga(Base):
    __tablename__ = "controle_carga"
    __table_args__ = (
        Index("idx_carga_fonte", "id_fonte"),
        Index("idx_carga_tabela", "tabela_destino"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_fonte: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCHEMA}.dim_fonte.id_fonte"), nullable=False)
    tabela_destino: Mapped[str] = mapped_column(String(60), nullable=False)
    data_referencia: Mapped[Optional[date]] = mapped_column(Date)
    registros_brutos: Mapped[Optional[int]] = mapped_column(Integer)
    registros_inseridos: Mapped[Optional[int]] = mapped_column(Integer)
    registros_atualizados: Mapped[Optional[int]] = mapped_column(Integer)
    registros_erros: Mapped[Optional[int]] = mapped_column(Integer)
    arquivo_origem: Mapped[Optional[str]] = mapped_column(Text)
    hash_arquivo: Mapped[Optional[str]] = mapped_column(String(64))
    duracao_segundos: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="Sucesso")
    erro_mensagem: Mapped[Optional[str]] = mapped_column(Text)
    executado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
