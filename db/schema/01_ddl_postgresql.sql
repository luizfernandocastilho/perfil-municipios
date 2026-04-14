-- ============================================================================
-- PERFIL MUNICÍPIOS BRASILEIROS — Schema Dimensional (PostgreSQL 16+ / PostGIS)
-- Versão: 1.0.0
-- Data: 2026-04-13
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- 0. EXTENSÕES E CONFIGURAÇÕES
-- ────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- busca por similaridade de texto
CREATE EXTENSION IF NOT EXISTS unaccent;      -- normalizar acentos em buscas

-- Schema dedicado
CREATE SCHEMA IF NOT EXISTS municipios;
SET search_path TO municipios, public;

-- ────────────────────────────────────────────────────────────────────────────
-- 1. TABELAS DE DIMENSÃO
-- ────────────────────────────────────────────────────────────────────────────

-- 1.1 Dimensão: Regiões e UFs (hierarquia territorial)
CREATE TABLE dim_regiao (
    codigo_regiao   SMALLINT    PRIMARY KEY,
    nome            VARCHAR(20) NOT NULL  -- Norte, Nordeste, Sudeste, Sul, Centro-Oeste
);

CREATE TABLE dim_uf (
    codigo_uf       SMALLINT    PRIMARY KEY,
    sigla           VARCHAR(2)  NOT NULL UNIQUE,
    nome            VARCHAR(50) NOT NULL,
    codigo_regiao   SMALLINT    NOT NULL REFERENCES dim_regiao(codigo_regiao),
    geom            GEOMETRY(MultiPolygon, 4326)
);

-- 1.2 Dimensão: Município (tabela central do sistema)
CREATE TABLE dim_municipio (
    codigo_ibge         VARCHAR(7)      PRIMARY KEY,   -- 7 dígitos (2 UF + 5 município)
    nome                VARCHAR(120)    NOT NULL,
    nome_normalizado    VARCHAR(120)    NOT NULL,       -- sem acentos, lowercase (busca)
    codigo_uf           SMALLINT        NOT NULL REFERENCES dim_uf(codigo_uf),
    codigo_mesorregiao  INTEGER,
    nome_mesorregiao    VARCHAR(120),
    codigo_microrregiao INTEGER,
    nome_microrregiao   VARCHAR(120),
    codigo_regiao_imediata  INTEGER,
    nome_regiao_imediata    VARCHAR(150),
    codigo_regiao_intermediaria INTEGER,
    nome_regiao_intermediaria   VARCHAR(150),
    capital             BOOLEAN         DEFAULT FALSE,
    area_km2            DECIMAL(12,3),
    geom                GEOMETRY(MultiPolygon, 4326),
    centroide           GEOMETRY(Point, 4326),
    created_at          TIMESTAMP       DEFAULT NOW(),
    updated_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_municipio_uf ON dim_municipio(codigo_uf);
CREATE INDEX idx_municipio_nome_trgm ON dim_municipio USING gin(nome_normalizado gin_trgm_ops);
CREATE INDEX idx_municipio_geom ON dim_municipio USING gist(geom);
CREATE INDEX idx_municipio_centroide ON dim_municipio USING gist(centroide);

-- 1.3 Dimensão: Partido Político
CREATE TABLE dim_partido (
    id_partido      SERIAL          PRIMARY KEY,
    sigla           VARCHAR(25)     NOT NULL,
    nome            VARCHAR(200)    NOT NULL,
    numero          SMALLINT        NOT NULL,
    data_criacao    DATE,
    situacao        VARCHAR(30)     DEFAULT 'Ativo',  -- Ativo, Extinto, Incorporado
    -- Partidos podem mudar de nome/sigla, manter histórico
    vigencia_inicio DATE            NOT NULL DEFAULT '1900-01-01',
    vigencia_fim    DATE,
    UNIQUE(sigla, vigencia_inicio)
);

CREATE INDEX idx_partido_sigla ON dim_partido(sigla);
CREATE INDEX idx_partido_numero ON dim_partido(numero);

-- 1.4 Dimensão: Parlamentar / Candidato
CREATE TABLE dim_parlamentar (
    id_parlamentar      SERIAL          PRIMARY KEY,
    cpf_hash            VARCHAR(64),            -- SHA-256 do CPF para deduplicação cross-source
    titulo_eleitor      VARCHAR(20),
    nome_completo       VARCHAR(200)    NOT NULL,
    nome_urna           VARCHAR(100),
    nome_social         VARCHAR(200),
    data_nascimento     DATE,
    genero              VARCHAR(20),
    raca_cor            VARCHAR(30),
    grau_instrucao      VARCHAR(50),
    naturalidade_ibge   VARCHAR(7)      REFERENCES dim_municipio(codigo_ibge),
    email               VARCHAR(200),
    -- Vínculo partidário atual (o histórico fica em dim_filiacao_partidaria)
    partido_atual_id    INTEGER         REFERENCES dim_partido(id_partido),
    foto_url            TEXT,
    created_at          TIMESTAMP       DEFAULT NOW(),
    updated_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_parlamentar_cpf ON dim_parlamentar(cpf_hash);
CREATE INDEX idx_parlamentar_nome_trgm ON dim_parlamentar USING gin(nome_completo gin_trgm_ops);

-- 1.5 Dimensão: Cargo Eletivo
CREATE TABLE dim_cargo (
    id_cargo        SERIAL          PRIMARY KEY,
    codigo_tse      SMALLINT        UNIQUE,
    nome            VARCHAR(50)     NOT NULL,   -- Prefeito, Vereador, Dep. Estadual, Dep. Federal, Senador, Governador, Presidente
    esfera          VARCHAR(20)     NOT NULL,   -- Municipal, Estadual, Federal
    abrangencia     VARCHAR(20)     NOT NULL    -- Município, Estado, Nacional
);

INSERT INTO dim_cargo (codigo_tse, nome, esfera, abrangencia) VALUES
    (11, 'Prefeito',              'Municipal', 'Município'),
    (12, 'Vice-Prefeito',         'Municipal', 'Município'),
    (13, 'Vereador',              'Municipal', 'Município'),
    (3,  'Governador',            'Estadual',  'Estado'),
    (4,  'Vice-Governador',       'Estadual',  'Estado'),
    (7,  'Deputado Estadual',     'Estadual',  'Estado'),
    (8,  'Deputado Distrital',    'Estadual',  'Estado'),
    (6,  'Deputado Federal',      'Federal',   'Estado'),
    (5,  'Senador',               'Federal',   'Estado'),
    (1,  'Presidente',            'Federal',   'Nacional'),
    (2,  'Vice-Presidente',       'Federal',   'Nacional');

-- 1.6 Dimensão: Eleição
CREATE TABLE dim_eleicao (
    id_eleicao      SERIAL          PRIMARY KEY,
    ano             SMALLINT        NOT NULL,
    tipo            VARCHAR(30)     NOT NULL,   -- Ordinária, Suplementar
    descricao       VARCHAR(100),               -- "Eleições Municipais 2024"
    data_1turno     DATE,
    data_2turno     DATE,
    UNIQUE(ano, tipo)
);

-- 1.7 Dimensão: Função Orçamentária (para emendas e finanças)
CREATE TABLE dim_funcao_orcamentaria (
    codigo_funcao       VARCHAR(5)      PRIMARY KEY,
    nome_funcao         VARCHAR(100)    NOT NULL,   -- Saúde, Educação, Transporte...
    codigo_subfuncao    VARCHAR(5),
    nome_subfuncao      VARCHAR(100)
);

-- 1.8 Dimensão: Tempo (calendário para facilitar queries)
CREATE TABLE dim_tempo (
    data                DATE            PRIMARY KEY,
    ano                 SMALLINT        NOT NULL,
    mes                 SMALLINT        NOT NULL,
    trimestre           SMALLINT        NOT NULL,
    semestre            SMALLINT        NOT NULL,
    dia_semana          SMALLINT        NOT NULL,
    nome_mes            VARCHAR(15)     NOT NULL,
    ano_mes             VARCHAR(7)      NOT NULL     -- '2024-01'
);

-- Popular dim_tempo de 2000 a 2035
INSERT INTO dim_tempo (data, ano, mes, trimestre, semestre, dia_semana, nome_mes, ano_mes)
SELECT
    d::date,
    EXTRACT(YEAR FROM d)::smallint,
    EXTRACT(MONTH FROM d)::smallint,
    EXTRACT(QUARTER FROM d)::smallint,
    CASE WHEN EXTRACT(MONTH FROM d) <= 6 THEN 1 ELSE 2 END::smallint,
    EXTRACT(DOW FROM d)::smallint,
    TO_CHAR(d, 'TMMonth'),
    TO_CHAR(d, 'YYYY-MM')
FROM generate_series('2000-01-01'::date, '2035-12-31'::date, '1 day'::interval) d;

-- 1.9 Dimensão: Fonte de Dados (rastreabilidade/linhagem)
CREATE TABLE dim_fonte (
    id_fonte        SERIAL          PRIMARY KEY,
    codigo          VARCHAR(10)     NOT NULL UNIQUE,  -- G01, E01, P01...
    nome            VARCHAR(100)    NOT NULL,
    orgao           VARCHAR(100),
    url             TEXT,
    formato         VARCHAR(50),
    frequencia      VARCHAR(30)
);


-- ────────────────────────────────────────────────────────────────────────────
-- 2. TABELAS DE FATO
-- ────────────────────────────────────────────────────────────────────────────

-- 2.1 Fato: Candidatura (registro de cada candidatura)
CREATE TABLE fato_candidatura (
    id                  BIGSERIAL       PRIMARY KEY,
    id_eleicao          INTEGER         NOT NULL REFERENCES dim_eleicao(id_eleicao),
    id_parlamentar      INTEGER         NOT NULL REFERENCES dim_parlamentar(id_parlamentar),
    id_cargo            INTEGER         NOT NULL REFERENCES dim_cargo(id_cargo),
    id_partido          INTEGER         NOT NULL REFERENCES dim_partido(id_partido),
    numero_candidato    INTEGER,
    codigo_ibge         VARCHAR(7)      REFERENCES dim_municipio(codigo_ibge),  -- NULL para cargos estaduais/federais
    codigo_uf           SMALLINT        REFERENCES dim_uf(codigo_uf),
    coligacao           VARCHAR(300),
    situacao_candidatura VARCHAR(30),    -- Apto, Inapto, Indeferido
    situacao_turno      VARCHAR(30),     -- Eleito, Não Eleito, 2º Turno, Suplente
    nome_urna           VARCHAR(100),
    despesa_campanha    DECIMAL(15,2),
    bens_declarados     DECIMAL(15,2),
    id_fonte            INTEGER         REFERENCES dim_fonte(id_fonte),
    created_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_candidatura_eleicao ON fato_candidatura(id_eleicao);
CREATE INDEX idx_candidatura_municipio ON fato_candidatura(codigo_ibge);
CREATE INDEX idx_candidatura_parlamentar ON fato_candidatura(id_parlamentar);
CREATE INDEX idx_candidatura_cargo ON fato_candidatura(id_cargo);

-- 2.2 Fato: Votação (votos por candidato por município/zona/seção)
CREATE TABLE fato_votacao (
    id                  BIGSERIAL       PRIMARY KEY,
    id_eleicao          INTEGER         NOT NULL REFERENCES dim_eleicao(id_eleicao),
    turno               SMALLINT        NOT NULL DEFAULT 1,
    id_cargo            INTEGER         NOT NULL REFERENCES dim_cargo(id_cargo),
    id_parlamentar      INTEGER         NOT NULL REFERENCES dim_parlamentar(id_parlamentar),
    id_partido          INTEGER         NOT NULL REFERENCES dim_partido(id_partido),
    codigo_ibge         VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    zona_eleitoral      SMALLINT,
    votos               INTEGER         NOT NULL DEFAULT 0,
    percentual_votos    DECIMAL(6,4),    -- % sobre válidos naquele município
    situacao            VARCHAR(30),     -- Eleito, Não Eleito, 2º Turno
    id_fonte            INTEGER         REFERENCES dim_fonte(id_fonte),
    created_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_votacao_eleicao_mun ON fato_votacao(id_eleicao, codigo_ibge);
CREATE INDEX idx_votacao_parlamentar ON fato_votacao(id_parlamentar);
CREATE INDEX idx_votacao_cargo ON fato_votacao(id_cargo);
CREATE INDEX idx_votacao_partido ON fato_votacao(id_partido);

-- 2.3 Fato: Emenda Parlamentar
CREATE TABLE fato_emenda (
    id                  BIGSERIAL       PRIMARY KEY,
    ano_loa             SMALLINT        NOT NULL,
    numero_emenda       VARCHAR(30),
    tipo_emenda         VARCHAR(40)     NOT NULL,       -- Individual, Bancada, Comissão, Relator, Pix
    id_parlamentar      INTEGER         REFERENCES dim_parlamentar(id_parlamentar),
    nome_autor          VARCHAR(200),                    -- backup se parlamentar não mapeado
    codigo_ibge         VARCHAR(7)      REFERENCES dim_municipio(codigo_ibge),
    codigo_uf           SMALLINT        REFERENCES dim_uf(codigo_uf),
    codigo_funcao       VARCHAR(5)      REFERENCES dim_funcao_orcamentaria(codigo_funcao),
    programa            VARCHAR(200),
    acao                VARCHAR(200),
    valor_empenhado     DECIMAL(15,2)   DEFAULT 0,
    valor_liquidado     DECIMAL(15,2)   DEFAULT 0,
    valor_pago          DECIMAL(15,2)   DEFAULT 0,
    valor_resto_pagar   DECIMAL(15,2)   DEFAULT 0,
    situacao            VARCHAR(50),                     -- Paga, Empenhada, Cancelada
    beneficiario_cnpj   VARCHAR(20),
    beneficiario_nome   VARCHAR(200),
    id_fonte            INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga          TIMESTAMP       DEFAULT NOW(),
    created_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_emenda_municipio ON fato_emenda(codigo_ibge);
CREATE INDEX idx_emenda_parlamentar ON fato_emenda(id_parlamentar);
CREATE INDEX idx_emenda_ano ON fato_emenda(ano_loa);
CREATE INDEX idx_emenda_tipo ON fato_emenda(tipo_emenda);
CREATE INDEX idx_emenda_funcao ON fato_emenda(codigo_funcao);

-- 2.4 Fato: Obra do PAC
CREATE TABLE fato_obra_pac (
    id                  BIGSERIAL       PRIMARY KEY,
    id_obra_externo     VARCHAR(50),                     -- ID no sistema de origem
    codigo_ibge         VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    nome_obra           VARCHAR(500),
    descricao           TEXT,
    eixo                VARCHAR(80),                     -- Transporte, Saúde, Educação, Água, Energia
    subeixo             VARCHAR(120),
    programa            VARCHAR(200),
    executor            VARCHAR(200),                    -- Empresa ou órgão executor
    valor_total         DECIMAL(15,2),
    valor_executado     DECIMAL(15,2),
    pct_execucao_fisica DECIMAL(5,2),
    pct_execucao_financeira DECIMAL(5,2),
    status              VARCHAR(40),                     -- Em licitação, Em execução, Concluída, Paralisada
    data_inicio         DATE,
    data_previsao_fim   DATE,
    data_conclusao      DATE,
    latitude            DECIMAL(10,7),
    longitude           DECIMAL(10,7),
    id_fonte            INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga          TIMESTAMP       DEFAULT NOW(),
    created_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_obra_municipio ON fato_obra_pac(codigo_ibge);
CREATE INDEX idx_obra_eixo ON fato_obra_pac(eixo);
CREATE INDEX idx_obra_status ON fato_obra_pac(status);

-- 2.5 Fato: Finanças Municipais (SICONFI / Finbra)
CREATE TABLE fato_financas (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    populacao_ref           INTEGER,                     -- população usada para per capita
    -- Receitas
    receita_total           DECIMAL(15,2),
    receita_corrente        DECIMAL(15,2),
    receita_tributaria      DECIMAL(15,2),
    receita_iss             DECIMAL(15,2),
    receita_iptu            DECIMAL(15,2),
    receita_itbi            DECIMAL(15,2),
    receita_transferencias  DECIMAL(15,2),
    receita_fpm             DECIMAL(15,2),
    receita_icms            DECIMAL(15,2),
    receita_fundeb          DECIMAL(15,2),
    receita_capital         DECIMAL(15,2),
    -- Despesas
    despesa_total           DECIMAL(15,2),
    despesa_corrente        DECIMAL(15,2),
    despesa_pessoal         DECIMAL(15,2),
    despesa_custeio         DECIMAL(15,2),
    despesa_capital         DECIMAL(15,2),
    despesa_investimento    DECIMAL(15,2),
    -- Despesas por função
    despesa_saude           DECIMAL(15,2),
    despesa_educacao        DECIMAL(15,2),
    despesa_assistencia     DECIMAL(15,2),
    despesa_urbanismo       DECIMAL(15,2),
    despesa_seguranca       DECIMAL(15,2),
    despesa_saneamento      DECIMAL(15,2),
    -- Indicadores fiscais
    pct_pessoal_rcl         DECIMAL(5,2),                -- % pessoal / receita corrente líquida
    pct_saude               DECIMAL(5,2),                -- % aplicado em saúde
    pct_educacao            DECIMAL(5,2),                -- % aplicado em educação
    superavit_primario      DECIMAL(15,2),
    divida_consolidada      DECIMAL(15,2),
    capag                   CHAR(1),                     -- A, B, C, D
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW(),
    UNIQUE(codigo_ibge, ano)
);

CREATE INDEX idx_financas_municipio ON fato_financas(codigo_ibge);
CREATE INDEX idx_financas_ano ON fato_financas(ano);

-- 2.6 Fato: Demografia / Indicadores IBGE
CREATE TABLE fato_demografia (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano_referencia          SMALLINT        NOT NULL,
    fonte_dado              VARCHAR(30),                 -- Censo, Estimativa, PNAD
    -- População
    populacao_total         INTEGER,
    populacao_urbana        INTEGER,
    populacao_rural         INTEGER,
    populacao_masculina     INTEGER,
    populacao_feminina      INTEGER,
    densidade_demografica   DECIMAL(10,2),
    taxa_urbanizacao        DECIMAL(5,2),
    -- Economia
    pib_total               DECIMAL(15,2),               -- em mil reais
    pib_per_capita          DECIMAL(12,2),
    pib_agropecuaria        DECIMAL(15,2),
    pib_industria           DECIMAL(15,2),
    pib_servicos            DECIMAL(15,2),
    pib_administracao       DECIMAL(15,2),
    -- Desenvolvimento Humano
    idhm                    DECIMAL(5,4),
    idhm_educacao           DECIMAL(5,4),
    idhm_renda              DECIMAL(5,4),
    idhm_longevidade        DECIMAL(5,4),
    gini                    DECIMAL(5,4),
    -- Renda
    salario_medio_mensal    DECIMAL(10,2),
    renda_per_capita        DECIMAL(10,2),
    pct_pobreza             DECIMAL(5,2),
    pct_extrema_pobreza     DECIMAL(5,2),
    -- Trabalho
    taxa_ocupacao           DECIMAL(5,2),
    empregos_formais        INTEGER,
    -- Outros
    taxa_mortalidade_infantil DECIMAL(6,2),
    esperanca_vida          DECIMAL(4,1),
    taxa_analfabetismo      DECIMAL(5,2),
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW(),
    UNIQUE(codigo_ibge, ano_referencia, fonte_dado)
);

CREATE INDEX idx_demografia_municipio ON fato_demografia(codigo_ibge);
CREATE INDEX idx_demografia_ano ON fato_demografia(ano_referencia);

-- 2.7 Fato: Transferências da União
CREATE TABLE fato_transferencia (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    mes                     SMALLINT,                    -- NULL se dado anual
    tipo_transferencia      VARCHAR(60)     NOT NULL,    -- FPM, FUNDEB, CFEM, Royalties, SUS, FNDE
    programa                VARCHAR(200),
    valor                   DECIMAL(15,2)   NOT NULL,
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_transf_municipio ON fato_transferencia(codigo_ibge);
CREATE INDEX idx_transf_tipo ON fato_transferencia(tipo_transferencia);
CREATE INDEX idx_transf_ano ON fato_transferencia(ano);

-- 2.8 Fato: Indicadores de Saúde
CREATE TABLE fato_saude (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    -- Atenção Básica
    cobertura_esf           DECIMAL(5,2),                -- % cobertura Estratégia Saúde da Família
    cobertura_acs           DECIMAL(5,2),
    equipes_esf             INTEGER,
    -- Estabelecimentos
    total_estabelecimentos  INTEGER,
    leitos_sus              INTEGER,
    leitos_uti              INTEGER,
    -- Indicadores
    internacoes_sus         INTEGER,
    obitos_geral            INTEGER,
    nascidos_vivos          INTEGER,
    mortalidade_infantil    DECIMAL(6,2),
    cobertura_vacinal       DECIMAL(5,2),
    -- Repasses
    repasse_fns_total       DECIMAL(15,2),
    repasse_pab             DECIMAL(15,2),
    repasse_mac             DECIMAL(15,2),
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW(),
    UNIQUE(codigo_ibge, ano)
);

CREATE INDEX idx_saude_municipio ON fato_saude(codigo_ibge);

-- 2.9 Fato: Indicadores de Educação
CREATE TABLE fato_educacao (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    -- Infraestrutura
    total_escolas           INTEGER,
    escolas_municipais      INTEGER,
    escolas_estaduais       INTEGER,
    escolas_federais        INTEGER,
    escolas_privadas        INTEGER,
    -- Matrículas
    matriculas_total        INTEGER,
    matriculas_creche       INTEGER,
    matriculas_pre_escola   INTEGER,
    matriculas_fundamental  INTEGER,
    matriculas_medio        INTEGER,
    matriculas_eja          INTEGER,
    -- Docentes
    total_docentes          INTEGER,
    docentes_superior       INTEGER,          -- com nível superior
    -- Qualidade
    ideb_anos_iniciais      DECIMAL(3,1),
    ideb_anos_finais        DECIMAL(3,1),
    taxa_aprovacao          DECIMAL(5,2),
    taxa_abandono           DECIMAL(5,2),
    taxa_distorcao_idade    DECIMAL(5,2),
    -- Repasses
    repasse_fnde_total      DECIMAL(15,2),
    repasse_pnae            DECIMAL(15,2),    -- merenda
    repasse_pdde            DECIMAL(15,2),    -- dinheiro direto na escola
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW(),
    UNIQUE(codigo_ibge, ano)
);

CREATE INDEX idx_educacao_municipio ON fato_educacao(codigo_ibge);

-- 2.10 Fato: Emprego e Economia Local
CREATE TABLE fato_emprego (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    mes                     SMALLINT,                    -- NULL se dado anual (RAIS)
    fonte_dado              VARCHAR(20),                 -- CAGED, RAIS
    -- Saldos CAGED (mensal)
    admissoes               INTEGER,
    desligamentos           INTEGER,
    saldo_emprego           INTEGER,
    -- Estoque RAIS (anual)
    estoque_empregos        INTEGER,
    massa_salarial          DECIMAL(15,2),
    salario_medio           DECIMAL(10,2),
    total_estabelecimentos  INTEGER,
    -- Programas Sociais
    familias_cadastro_unico INTEGER,
    beneficiarios_bolsa_familia INTEGER,
    valor_bolsa_familia     DECIMAL(15,2),
    beneficiarios_bpc       INTEGER,
    valor_bpc               DECIMAL(15,2),
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_emprego_municipio ON fato_emprego(codigo_ibge);
CREATE INDEX idx_emprego_ano_mes ON fato_emprego(ano, mes);

-- 2.11 Fato: Infraestrutura Municipal
CREATE TABLE fato_infraestrutura (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    -- Saneamento (SNIS)
    cobertura_agua          DECIMAL(5,2),    -- % população atendida
    cobertura_esgoto        DECIMAL(5,2),
    tratamento_esgoto       DECIMAL(5,2),    -- % esgoto tratado
    perdas_agua             DECIMAL(5,2),    -- % perdas na distribuição
    cobertura_coleta_lixo   DECIMAL(5,2),
    -- Energia (ANEEL)
    consumidores_energia    INTEGER,
    consumo_energia_mwh     DECIMAL(12,2),
    geracao_distribuida_kw  DECIMAL(12,2),
    -- Telecomunicações (ANATEL)
    acessos_banda_larga     INTEGER,
    acessos_movel           INTEGER,
    cobertura_4g            BOOLEAN,
    cobertura_5g            BOOLEAN,
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW(),
    UNIQUE(codigo_ibge, ano)
);

CREATE INDEX idx_infra_municipio ON fato_infraestrutura(codigo_ibge);

-- 2.12 Fato: Segurança Pública
CREATE TABLE fato_seguranca (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    mes                     SMALLINT,
    homicidios              INTEGER,
    latrocinios             INTEGER,
    roubos                  INTEGER,
    furtos                  INTEGER,
    trafico_drogas          INTEGER,
    taxa_homicidios_100k    DECIMAL(6,2),
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_seguranca_municipio ON fato_seguranca(codigo_ibge);

-- 2.13 Fato: Meio Ambiente
CREATE TABLE fato_meio_ambiente (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    desmatamento_km2        DECIMAL(10,3),
    desmatamento_acumulado  DECIMAL(12,3),
    area_protegida_km2      DECIMAL(10,3),
    pct_area_protegida      DECIMAL(5,2),
    focos_incendio          INTEGER,
    bioma_predominante      VARCHAR(30),     -- Amazônia, Cerrado, Mata Atlântica, Caatinga, Pampa, Pantanal
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_ambiente_municipio ON fato_meio_ambiente(codigo_ibge);

-- 2.14 Fato: Gestão Municipal (MUNIC/IBGE)
CREATE TABLE fato_gestao_municipal (
    id                      BIGSERIAL       PRIMARY KEY,
    codigo_ibge             VARCHAR(7)      NOT NULL REFERENCES dim_municipio(codigo_ibge),
    ano                     SMALLINT        NOT NULL,
    nome_prefeito           VARCHAR(200),
    partido_prefeito        VARCHAR(25),
    vice_prefeito           VARCHAR(200),
    -- Estrutura administrativa
    tem_plano_diretor       BOOLEAN,
    tem_conselho_saude      BOOLEAN,
    tem_conselho_educacao   BOOLEAN,
    tem_conselho_meio_ambiente BOOLEAN,
    tem_guarda_municipal    BOOLEAN,
    total_servidores        INTEGER,
    servidores_estatutarios INTEGER,
    servidores_comissionados INTEGER,
    -- Legislativo municipal
    total_vereadores        SMALLINT,
    id_fonte                INTEGER         REFERENCES dim_fonte(id_fonte),
    data_carga              TIMESTAMP       DEFAULT NOW(),
    created_at              TIMESTAMP       DEFAULT NOW(),
    UNIQUE(codigo_ibge, ano)
);

CREATE INDEX idx_gestao_municipio ON fato_gestao_municipal(codigo_ibge);


-- ────────────────────────────────────────────────────────────────────────────
-- 3. TABELAS AUXILIARES / PONTE
-- ────────────────────────────────────────────────────────────────────────────

-- 3.1 Histórico de Filiação Partidária
CREATE TABLE hist_filiacao_partidaria (
    id                  BIGSERIAL       PRIMARY KEY,
    id_parlamentar      INTEGER         NOT NULL REFERENCES dim_parlamentar(id_parlamentar),
    id_partido          INTEGER         NOT NULL REFERENCES dim_partido(id_partido),
    data_filiacao       DATE,
    data_desfiliacao    DATE,
    motivo              VARCHAR(100)
);

CREATE INDEX idx_filiacao_parlamentar ON hist_filiacao_partidaria(id_parlamentar);

-- 3.2 Mandatos (vínculo parlamentar-cargo-período)
CREATE TABLE hist_mandato (
    id                  BIGSERIAL       PRIMARY KEY,
    id_parlamentar      INTEGER         NOT NULL REFERENCES dim_parlamentar(id_parlamentar),
    id_cargo            INTEGER         NOT NULL REFERENCES dim_cargo(id_cargo),
    id_eleicao          INTEGER         NOT NULL REFERENCES dim_eleicao(id_eleicao),
    codigo_ibge         VARCHAR(7)      REFERENCES dim_municipio(codigo_ibge),  -- para cargos municipais
    codigo_uf           SMALLINT        REFERENCES dim_uf(codigo_uf),
    id_partido          INTEGER         REFERENCES dim_partido(id_partido),
    inicio_mandato      DATE,
    fim_mandato         DATE,
    situacao            VARCHAR(30)     DEFAULT 'Exercício'  -- Exercício, Licenciado, Cassado, Renunciou
);

CREATE INDEX idx_mandato_parlamentar ON hist_mandato(id_parlamentar);
CREATE INDEX idx_mandato_municipio ON hist_mandato(codigo_ibge);

-- 3.3 Controle de Carga (linhagem de dados)
CREATE TABLE controle_carga (
    id                  BIGSERIAL       PRIMARY KEY,
    id_fonte            INTEGER         NOT NULL REFERENCES dim_fonte(id_fonte),
    tabela_destino      VARCHAR(60)     NOT NULL,
    data_referencia     DATE,
    registros_brutos    INTEGER,
    registros_inseridos INTEGER,
    registros_atualizados INTEGER,
    registros_erros     INTEGER,
    arquivo_origem      TEXT,
    hash_arquivo        VARCHAR(64),         -- SHA-256 para detectar mudanças
    duracao_segundos    INTEGER,
    status              VARCHAR(20)     DEFAULT 'Sucesso',  -- Sucesso, Falha, Parcial
    erro_mensagem       TEXT,
    executado_em        TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_carga_fonte ON controle_carga(id_fonte);
CREATE INDEX idx_carga_tabela ON controle_carga(tabela_destino);
CREATE INDEX idx_carga_data ON controle_carga(executado_em);


-- ────────────────────────────────────────────────────────────────────────────
-- 4. VIEWS MATERIALIZADAS (para performance no frontend)
-- ────────────────────────────────────────────────────────────────────────────

-- 4.1 Perfil resumido do município (usado na página de perfil)
CREATE MATERIALIZED VIEW mv_perfil_municipio AS
SELECT
    m.codigo_ibge,
    m.nome,
    u.sigla AS uf,
    u.nome AS estado,
    r.nome AS regiao,
    m.area_km2,
    m.capital,
    -- Último dado demográfico
    d.populacao_total,
    d.pib_per_capita,
    d.idhm,
    d.gini,
    d.ano_referencia AS ano_dado_demografico,
    -- Último dado financeiro
    f.receita_total,
    f.despesa_total,
    f.capag,
    f.ano AS ano_dado_financeiro,
    -- Prefeito atual
    g.nome_prefeito,
    g.partido_prefeito,
    g.total_vereadores
FROM dim_municipio m
JOIN dim_uf u ON m.codigo_uf = u.codigo_uf
JOIN dim_regiao r ON u.codigo_regiao = r.codigo_regiao
LEFT JOIN LATERAL (
    SELECT * FROM fato_demografia fd
    WHERE fd.codigo_ibge = m.codigo_ibge
    ORDER BY fd.ano_referencia DESC LIMIT 1
) d ON TRUE
LEFT JOIN LATERAL (
    SELECT * FROM fato_financas ff
    WHERE ff.codigo_ibge = m.codigo_ibge
    ORDER BY ff.ano DESC LIMIT 1
) f ON TRUE
LEFT JOIN LATERAL (
    SELECT * FROM fato_gestao_municipal fg
    WHERE fg.codigo_ibge = m.codigo_ibge
    ORDER BY fg.ano DESC LIMIT 1
) g ON TRUE
WITH NO DATA;

CREATE UNIQUE INDEX idx_mv_perfil_codigo ON mv_perfil_municipio(codigo_ibge);

-- 4.2 Ranking de emendas por município
CREATE MATERIALIZED VIEW mv_emendas_por_municipio AS
SELECT
    codigo_ibge,
    ano_loa,
    COUNT(*)                    AS total_emendas,
    SUM(valor_empenhado)        AS total_empenhado,
    SUM(valor_pago)             AS total_pago,
    COUNT(DISTINCT id_parlamentar) AS total_parlamentares,
    COUNT(DISTINCT tipo_emenda)    AS tipos_emenda
FROM fato_emenda
WHERE codigo_ibge IS NOT NULL
GROUP BY codigo_ibge, ano_loa
WITH NO DATA;

CREATE UNIQUE INDEX idx_mv_emendas_mun_ano ON mv_emendas_por_municipio(codigo_ibge, ano_loa);


-- ────────────────────────────────────────────────────────────────────────────
-- 5. FUNCTIONS ÚTEIS
-- ────────────────────────────────────────────────────────────────────────────

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger nas dimensões editáveis
CREATE TRIGGER set_updated_at_municipio
    BEFORE UPDATE ON dim_municipio
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_parlamentar
    BEFORE UPDATE ON dim_parlamentar
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- Função para refresh de todas as materialized views
CREATE OR REPLACE FUNCTION refresh_all_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_perfil_municipio;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_emendas_por_municipio;
    -- Adicionar novas MVs aqui
END;
$$ LANGUAGE plpgsql;


-- ────────────────────────────────────────────────────────────────────────────
-- FIM DO DDL
-- ────────────────────────────────────────────────────────────────────────────
