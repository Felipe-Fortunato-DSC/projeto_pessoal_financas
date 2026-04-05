-- =============================================================================
-- DDL – Gestao Financeira Familiar
-- Banco: DuckDB (local) / MotherDuck (producao)
-- =============================================================================

-- Sequencias de ID
CREATE SEQUENCE IF NOT EXISTS seq_users        START 1;
CREATE SEQUENCE IF NOT EXISTS seq_salarios     START 1;
CREATE SEQUENCE IF NOT EXISTS seq_despesas     START 1;
CREATE SEQUENCE IF NOT EXISTS seq_investimentos START 1;
CREATE SEQUENCE IF NOT EXISTS seq_categorias   START 1;
CREATE SEQUENCE IF NOT EXISTS seq_tipos_inv    START 1;

-- Usuarios do sistema
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY DEFAULT nextval('seq_users'),
    nome       VARCHAR NOT NULL UNIQUE,
    senha_hash VARCHAR NOT NULL          -- SHA-256 da senha
);

-- Salarios mensais por usuario
CREATE TABLE IF NOT EXISTS salarios (
    id      INTEGER PRIMARY KEY DEFAULT nextval('seq_salarios'),
    user_id INTEGER NOT NULL,            -- FK → users.id
    mes     INTEGER NOT NULL,            -- 1-12
    ano     INTEGER NOT NULL,
    valor   DECIMAL(12, 2) NOT NULL,
    fonte   VARCHAR                      -- opcional: empresa, freelance, etc.
);

-- Despesas mensais por usuario
CREATE TABLE IF NOT EXISTS despesas (
    id        INTEGER PRIMARY KEY DEFAULT nextval('seq_despesas'),
    user_id   INTEGER NOT NULL,          -- FK → users.id
    mes       INTEGER NOT NULL,          -- 1-12
    ano       INTEGER NOT NULL,
    categoria VARCHAR NOT NULL,          -- referencia a categorias.nome
    descricao VARCHAR,                   -- descricao livre (opcional)
    valor     DECIMAL(12, 2) NOT NULL
);

-- Aportes de investimento
CREATE TABLE IF NOT EXISTS investimentos (
    id      INTEGER PRIMARY KEY DEFAULT nextval('seq_investimentos'),
    user_id INTEGER NOT NULL,            -- FK → users.id
    tipo    VARCHAR NOT NULL,            -- referencia a tipos_investimento.nome
    valor   DECIMAL(12, 2) NOT NULL,
    data    DATE NOT NULL
);

-- Categorias de despesas (gerenciaveis pelo usuario)
CREATE TABLE IF NOT EXISTS categorias (
    id   INTEGER PRIMARY KEY DEFAULT nextval('seq_categorias'),
    nome VARCHAR NOT NULL UNIQUE
);

-- Tipos de investimento (gerenciaveis pelo usuario)
CREATE TABLE IF NOT EXISTS tipos_investimento (
    id   INTEGER PRIMARY KEY DEFAULT nextval('seq_tipos_inv'),
    nome VARCHAR NOT NULL UNIQUE
);

-- =============================================================================
-- Dados iniciais (seed)
-- =============================================================================

-- Usuarios (senha padrao: Moniqu&2019 — hash SHA-256)
INSERT INTO users (nome, senha_hash)
SELECT 'Monique Fortunato', sha256('Moniqu&2019')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE nome = 'Monique Fortunato');

INSERT INTO users (nome, senha_hash)
SELECT 'Felipe Fortunato', sha256('Moniqu&2019')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE nome = 'Felipe Fortunato');

-- Categorias
INSERT INTO categorias (nome)
SELECT unnest(['Moradia','Alimentacao','Transporte','Saude','Lazer',
               'Educacao','Vestuario','Servicos','Outros'])
WHERE NOT EXISTS (SELECT 1 FROM categorias);

-- Tipos de investimento
INSERT INTO tipos_investimento (nome)
SELECT unnest(['Previdencia Privada','Renda Fixa','Acoes',
               'Fundos Imobiliarios','Reserva de Emergencia','Outros'])
WHERE NOT EXISTS (SELECT 1 FROM tipos_investimento);
