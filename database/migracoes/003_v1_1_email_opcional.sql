-- Migração 003 (v1.1) — avaliação de Fernando Miranda: e-mail não deve ser obrigatório.
-- SQLite não altera CHECK de coluna existente: a tabela cliente é recriada preservando os dados.
PRAGMA foreign_keys = OFF;
BEGIN;
CREATE TABLE cliente_nova (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL CHECK (length(trim(nome)) BETWEEN 3 AND 80),
    telefone    TEXT    NOT NULL CHECK (length(telefone) BETWEEN 10 AND 11),
    email       TEXT    NOT NULL DEFAULT '' CHECK (email = '' OR email LIKE '%_@_%._%'),
    criado_em   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
INSERT INTO cliente_nova (id, nome, telefone, email, criado_em) SELECT id, nome, telefone, email, criado_em FROM cliente;
DROP TABLE cliente;
ALTER TABLE cliente_nova RENAME TO cliente;
CREATE INDEX IF NOT EXISTS ix_cliente_email ON cliente(email);
COMMIT;
PRAGMA foreign_keys = ON;
