-- =====================================================================
-- Doce Nuvem Cupcakes Gourmet — Projeto físico do banco de dados
-- SGBD: SQLite 3 (compatível com SQL padrão; migrável para PostgreSQL)
-- Valores monetários em CENTAVOS (INTEGER) para evitar erro de ponto flutuante.
-- Datas em texto ISO-8601 (UTC), padrão recomendado para SQLite.
-- =====================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS historico_status;
DROP TABLE IF EXISTS pagamento;
DROP TABLE IF EXISTS item_pedido;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS cliente;
DROP TABLE IF EXISTS zona_entrega;
DROP TABLE IF EXISTS cupcake;
DROP TABLE IF EXISTS categoria;
DROP TABLE IF EXISTS usuario_admin;

-- ---------------------------------------------------------------------
-- CATEGORIA: agrupa os cupcakes para os filtros da vitrine (US02)
-- ---------------------------------------------------------------------
CREATE TABLE categoria (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL UNIQUE CHECK (length(trim(nome)) BETWEEN 2 AND 40),
    slug        TEXT    NOT NULL UNIQUE CHECK (slug GLOB '[a-z]*')
);

-- ---------------------------------------------------------------------
-- CUPCAKE: produto exibido na vitrine (US01, US03)
-- ---------------------------------------------------------------------
CREATE TABLE cupcake (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id    INTEGER NOT NULL REFERENCES categoria(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    nome            TEXT    NOT NULL UNIQUE CHECK (length(trim(nome)) BETWEEN 2 AND 60),
    descricao       TEXT    NOT NULL CHECK (length(descricao) <= 500),
    ingredientes    TEXT    NOT NULL CHECK (length(ingredientes) <= 500),
    alergenicos     TEXT    NOT NULL DEFAULT '',
    preco_centavos  INTEGER NOT NULL CHECK (preco_centavos BETWEEN 100 AND 100000),
    cor_cobertura   TEXT    NOT NULL DEFAULT '#f4a6c0' CHECK (cor_cobertura GLOB '#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]'),
    ativo           INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);
CREATE INDEX ix_cupcake_categoria ON cupcake(categoria_id);

-- ---------------------------------------------------------------------
-- ZONA_ENTREGA: faixas de CEP atendidas, com valor e prazo (US08)
-- ---------------------------------------------------------------------
CREATE TABLE zona_entrega (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL UNIQUE,
    cep_inicio      INTEGER NOT NULL CHECK (cep_inicio BETWEEN 1000000 AND 99999999),
    cep_fim         INTEGER NOT NULL CHECK (cep_fim BETWEEN 1000000 AND 99999999),
    valor_centavos  INTEGER NOT NULL CHECK (valor_centavos >= 0),
    prazo_minutos   INTEGER NOT NULL CHECK (prazo_minutos BETWEEN 10 AND 240),
    CHECK (cep_inicio <= cep_fim)
);

-- ---------------------------------------------------------------------
-- CLIENTE: quem faz o pedido (sem senha no MVP: compra como convidado)
-- ---------------------------------------------------------------------
CREATE TABLE cliente (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL CHECK (length(trim(nome)) BETWEEN 3 AND 80),
    telefone    TEXT    NOT NULL CHECK (length(telefone) BETWEEN 10 AND 11),
    email       TEXT    NOT NULL CHECK (email LIKE '%_@_%._%'),
    criado_em   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX ix_cliente_email ON cliente(email);

-- ---------------------------------------------------------------------
-- PEDIDO: cabeçalho da compra (US04, US05, US06, US09, US10)
-- O endereço é gravado no pedido (cópia histórica) de propósito:
-- se o cliente mudar de endereço, o pedido antigo continua correto.
-- ---------------------------------------------------------------------
CREATE TABLE pedido (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo                  TEXT    NOT NULL UNIQUE CHECK (length(codigo) = 8),
    cliente_id              INTEGER NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
    zona_entrega_id         INTEGER NOT NULL REFERENCES zona_entrega(id) ON DELETE RESTRICT,
    status                  TEXT    NOT NULL DEFAULT 'AGUARDANDO_PAGAMENTO'
                            CHECK (status IN ('AGUARDANDO_PAGAMENTO','RECEBIDO','EM_PREPARO',
                                              'SAIU_PARA_ENTREGA','ENTREGUE','CANCELADO')),
    embalagem_presente      INTEGER NOT NULL DEFAULT 0 CHECK (embalagem_presente IN (0, 1)),
    mensagem_presente       TEXT    NOT NULL DEFAULT '' CHECK (length(mensagem_presente) <= 140),
    cep                     INTEGER NOT NULL,
    logradouro              TEXT    NOT NULL CHECK (length(trim(logradouro)) >= 3),
    numero                  TEXT    NOT NULL CHECK (length(trim(numero)) >= 1),
    bairro                  TEXT    NOT NULL CHECK (length(trim(bairro)) >= 2),
    complemento             TEXT    NOT NULL DEFAULT '',
    subtotal_centavos       INTEGER NOT NULL CHECK (subtotal_centavos > 0),
    embalagem_centavos      INTEGER NOT NULL DEFAULT 0 CHECK (embalagem_centavos >= 0),
    frete_centavos          INTEGER NOT NULL CHECK (frete_centavos >= 0),
    total_centavos          INTEGER NOT NULL,
    criado_em               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    atualizado_em           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (total_centavos = subtotal_centavos + embalagem_centavos + frete_centavos)
);
CREATE INDEX ix_pedido_status ON pedido(status);
CREATE INDEX ix_pedido_cliente ON pedido(cliente_id);

-- ---------------------------------------------------------------------
-- ITEM_PEDIDO: tabela associativa Pedido N:N Cupcake
-- preco_unitario é congelado no momento da compra.
-- ---------------------------------------------------------------------
CREATE TABLE item_pedido (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id               INTEGER NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    cupcake_id              INTEGER NOT NULL REFERENCES cupcake(id) ON DELETE RESTRICT,
    quantidade              INTEGER NOT NULL CHECK (quantidade BETWEEN 1 AND 50),
    preco_unitario_centavos INTEGER NOT NULL CHECK (preco_unitario_centavos > 0),
    subtotal_centavos       INTEGER NOT NULL,
    UNIQUE (pedido_id, cupcake_id),
    CHECK (subtotal_centavos = quantidade * preco_unitario_centavos)
);

-- ---------------------------------------------------------------------
-- PAGAMENTO: 1:1 com pedido (US07). Nunca armazena número de cartão:
-- guarda apenas os 4 últimos dígitos para conferência.
-- ---------------------------------------------------------------------
CREATE TABLE pagamento (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL UNIQUE REFERENCES pedido(id) ON DELETE CASCADE,
    metodo          TEXT    NOT NULL CHECK (metodo IN ('PIX', 'CARTAO')),
    status          TEXT    NOT NULL DEFAULT 'PENDENTE'
                    CHECK (status IN ('PENDENTE', 'APROVADO', 'RECUSADO', 'EXPIRADO')),
    codigo_pix      TEXT,
    cartao_final    TEXT    CHECK (cartao_final IS NULL OR (length(cartao_final) = 4 AND cartao_final GLOB '[0-9][0-9][0-9][0-9]')),
    motivo_recusa   TEXT    NOT NULL DEFAULT '',
    expira_em       TEXT,
    atualizado_em   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK ((metodo = 'PIX' AND codigo_pix IS NOT NULL) OR (metodo = 'CARTAO' AND codigo_pix IS NULL))
);

-- ---------------------------------------------------------------------
-- HISTORICO_STATUS: linha do tempo do pedido para o rastreio (US09)
-- ---------------------------------------------------------------------
CREATE TABLE historico_status (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id   INTEGER NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    status      TEXT    NOT NULL,
    data_hora   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX ix_historico_pedido ON historico_status(pedido_id);

-- ---------------------------------------------------------------------
-- USUARIO_ADMIN: acesso ao painel do lojista (US10). Senha só em hash.
-- ---------------------------------------------------------------------
CREATE TABLE usuario_admin (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     TEXT    NOT NULL UNIQUE CHECK (length(usuario) BETWEEN 3 AND 30),
    senha_hash  TEXT    NOT NULL
);
