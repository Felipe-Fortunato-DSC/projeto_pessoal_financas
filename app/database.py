"""
database.py
-----------
Conexão com DuckDB local ou MotherDuck, seguindo o mesmo padrão do TJ-Processos.
"""

import duckdb
import streamlit as st

from config import DB_LOCAL_PATH, CATEGORIAS_PADRAO
from app.utils import hash_password


@st.cache_resource
def _get_conn() -> tuple[duckdb.DuckDBPyConnection, str]:
    try:
        token = st.secrets["motherduck"]["token"]
        db    = st.secrets.get("MOTHERDUCK_DB", "financas")
        tmp   = duckdb.connect(f"md:?motherduck_token={token}")
        tmp.execute(f"CREATE DATABASE IF NOT EXISTS {db}")
        tmp.close()
        conn = duckdb.connect(f"md:{db}?motherduck_token={token}")
        return conn, "motherduck"
    except KeyError:
        conn = duckdb.connect(DB_LOCAL_PATH)
        return conn, "local"
    except Exception as e:
        st.error(f"Erro ao conectar ao MotherDuck: {e}")
        conn = duckdb.connect(DB_LOCAL_PATH)
        return conn, "local"


def get_connection() -> duckdb.DuckDBPyConnection:
    conn, _ = _get_conn()
    return conn


def db_mode() -> str:
    _, mode = _get_conn()
    return mode


def _exec(conn, sql: str, params=None) -> None:
    sql = sql.strip()
    if sql:
        conn.execute(sql, params or [])


def _seed_password() -> str:
    try:
        return st.secrets.get("SEED_PASSWORD", "")
    except Exception:
        import os
        return os.environ.get("SEED_PASSWORD", "")


def init_schema() -> None:
    conn = get_connection()

    for seq in ["seq_users", "seq_salarios", "seq_despesas",
                "seq_investimentos", "seq_categorias"]:
        _exec(conn, f"CREATE SEQUENCE IF NOT EXISTS {seq} START 1")

    # Migrações schema antigo
    try:
        cols = [r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='salarios'"
        ).fetchall()]
        if "valor" in cols:
            conn.execute("DROP TABLE salarios")
    except Exception:
        pass

    try:
        cols = [r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='investimentos'"
        ).fetchall()]
        if "data" in cols or "tipo" in cols:
            conn.execute("DROP TABLE investimentos")
    except Exception:
        pass

    try:
        cols = [r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='investimentos'"
        ).fetchall()]
        if cols and "origem" not in cols:
            conn.execute("ALTER TABLE investimentos ADD COLUMN origem VARCHAR")
    except Exception:
        pass

    # Migração coluna tipo — tenta SELECT direto para garantir que a coluna existe
    try:
        conn.execute("SELECT tipo FROM investimentos LIMIT 0")
    except Exception:
        try:
            conn.execute("ALTER TABLE investimentos ADD COLUMN tipo VARCHAR")
        except Exception:
            pass
        try:
            conn.execute("UPDATE investimentos SET tipo = 'entrada' WHERE tipo IS NULL")
        except Exception:
            pass

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

    # Seed usuários
    pwd = _seed_password()
    for u in [("Monique Fortunato", pwd), ("Felipe Fortunato", pwd)]:
        conn.execute(
            "INSERT INTO users (nome, senha_hash) SELECT ?, ? "
            "WHERE NOT EXISTS (SELECT 1 FROM users WHERE nome = ?)",
            [u[0], hash_password(u[1]), u[0]],
        )

    # Seed categorias (apenas insere as que ainda não existem)
    for cat in CATEGORIAS_PADRAO:
        conn.execute(
            "INSERT INTO categorias (nome) SELECT ? WHERE NOT EXISTS "
            "(SELECT 1 FROM categorias WHERE nome = ?)",
            [cat, cat],
        )
