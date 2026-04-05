"""
database.py
-----------
Gerencia a conexão com DuckDB (local) ou MotherDuck (produção)
e inicializa o schema do banco de dados.
"""

import duckdb
import streamlit as st

from config import (
    DB_LOCAL_PATH, MOTHERDUCK_TOKEN, MOTHERDUCK_DB, USE_MOTHERDUCK,
    USUARIOS_INICIAIS, CATEGORIAS_PADRAO, CATEGORIAS_INVESTIMENTOS,
)
from app.utils import hash_password


def _exec(conn: duckdb.DuckDBPyConnection, sql: str, params=None) -> None:
    sql = sql.strip()
    if sql:
        conn.execute(sql, params or [])


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Retorna (e cacheia) a conexão com o banco.
    - LOCAL : DuckDB em arquivo  (data/financas.duckdb)
    - CLOUD : MotherDuck          (md:<db>?motherduck_token=<token>)
    """
    if USE_MOTHERDUCK:
        conn = duckdb.connect(
            f"md:{MOTHERDUCK_DB}?motherduck_token={MOTHERDUCK_TOKEN}"
        )
    else:
        conn = duckdb.connect(DB_LOCAL_PATH)

    _init_schema(conn)
    return conn


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Cria sequências, tabelas e registros iniciais caso não existam."""

    # -- Sequências ------------------------------------------------------------
    for seq in ["seq_users", "seq_salarios", "seq_despesas",
                "seq_investimentos", "seq_categorias"]:
        _exec(conn, f"CREATE SEQUENCE IF NOT EXISTS {seq} START 1")

    # -- Migração: salarios schema antigo (valor/fonte) → novo ----------------
    try:
        cols = [r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='salarios'"
        ).fetchall()]
        if "valor" in cols:
            conn.execute("DROP TABLE salarios")
    except Exception:
        pass

    # -- Migração: investimentos schema antigo (tipo/data) → novo -------------
    try:
        cols = [r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='investimentos'"
        ).fetchall()]
        if "data" in cols or "tipo" in cols:
            conn.execute("DROP TABLE investimentos")
    except Exception:
        pass

    # -- Migração: adiciona coluna 'origem' em investimentos se não existir ---
    try:
        cols = [r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='investimentos'"
        ).fetchall()]
        if cols and "origem" not in cols:
            conn.execute("ALTER TABLE investimentos ADD COLUMN origem VARCHAR")
    except Exception:
        pass

    # -- Tabelas ---------------------------------------------------------------
    _exec(conn, """
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY DEFAULT nextval('seq_users'),
            nome       VARCHAR NOT NULL UNIQUE,
            senha_hash VARCHAR NOT NULL
        )
    """)

    _exec(conn, """
        CREATE TABLE IF NOT EXISTS salarios (
            id          INTEGER PRIMARY KEY DEFAULT nextval('seq_salarios'),
            user_id     INTEGER NOT NULL,
            mes         INTEGER NOT NULL,
            ano         INTEGER NOT NULL,
            salario     DECIMAL(12, 2) NOT NULL DEFAULT 0,
            alimentacao DECIMAL(12, 2) NOT NULL DEFAULT 0,
            transporte  DECIMAL(12, 2) NOT NULL DEFAULT 0,
            ferias      DECIMAL(12, 2) NOT NULL DEFAULT 0,
            renda_extra DECIMAL(12, 2) NOT NULL DEFAULT 0,
            UNIQUE (user_id, mes, ano)
        )
    """)

    _exec(conn, """
        CREATE TABLE IF NOT EXISTS despesas (
            id        INTEGER PRIMARY KEY DEFAULT nextval('seq_despesas'),
            user_id   INTEGER NOT NULL,
            mes       INTEGER NOT NULL,
            ano       INTEGER NOT NULL,
            categoria VARCHAR NOT NULL,
            descricao VARCHAR,
            valor     DECIMAL(12, 2) NOT NULL
        )
    """)

    _exec(conn, """
        CREATE TABLE IF NOT EXISTS investimentos (
            id         INTEGER PRIMARY KEY DEFAULT nextval('seq_investimentos'),
            user_id    INTEGER NOT NULL,
            ano        INTEGER NOT NULL,
            mes        INTEGER NOT NULL,
            categoria  VARCHAR NOT NULL,
            origem     VARCHAR,
            valor      DECIMAL(12, 2) NOT NULL,
            observacao VARCHAR
        )
    """)

    _exec(conn, """
        CREATE TABLE IF NOT EXISTS categorias (
            id   INTEGER PRIMARY KEY DEFAULT nextval('seq_categorias'),
            nome VARCHAR NOT NULL UNIQUE
        )
    """)

    # -- Seed: usuários --------------------------------------------------------
    for u in USUARIOS_INICIAIS:
        conn.execute(
            "INSERT INTO users (nome, senha_hash) SELECT ?, ? "
            "WHERE NOT EXISTS (SELECT 1 FROM users WHERE nome = ?)",
            [u["nome"], hash_password(u["senha"]), u["nome"]],
        )

    # -- Categorias de despesas: sincroniza com config -------------------------
    conn.execute("DELETE FROM categorias")
    for cat in CATEGORIAS_PADRAO:
        conn.execute("INSERT INTO categorias (nome) VALUES (?)", [cat])
