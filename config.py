import os
from pathlib import Path

def _secret(key: str, default: str = "") -> str:
    """Lê de st.secrets (Streamlit Cloud) ou variável de ambiente, com fallback."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)

# ---------------------------------------------------------------------------
# Diretórios
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
# Local: DuckDB em arquivo
DB_LOCAL_PATH = str(DATA_DIR / "financas.duckdb")

# MotherDuck (produção): defina MOTHERDUCK_TOKEN no ambiente para ativar
MOTHERDUCK_TOKEN = _secret("MOTHERDUCK_TOKEN")
MOTHERDUCK_DB    = _secret("MOTHERDUCK_DB", "financas")
USE_MOTHERDUCK   = bool(MOTHERDUCK_TOKEN)

# ---------------------------------------------------------------------------
# Usuários iniciais (seed)
# Senha lida de variável de ambiente SEED_PASSWORD (Streamlit Secrets ou .env)
# ---------------------------------------------------------------------------
_SEED_PASSWORD = _secret("SEED_PASSWORD")

USUARIOS_INICIAIS = [
    {"nome": "Monique Fortunato", "senha": _SEED_PASSWORD},
    {"nome": "Felipe Fortunato",  "senha": _SEED_PASSWORD},
]

# ---------------------------------------------------------------------------
# Categorias padrão de despesas
# ---------------------------------------------------------------------------
CATEGORIAS_PADRAO = [
    "Inter", "XP", "BRB", "IPTU", "FUNESBOM",
    "Financiamento Imobiliário", "Luz", "Gás", "Água",
    "Seguro Residencial", "Faxina", "Lazer", "Condomínio",
]

# ---------------------------------------------------------------------------
# Categorias de investimento
# ---------------------------------------------------------------------------
CATEGORIAS_INVESTIMENTOS = [
    "Previdência Privada", "Renda Fixa", "Ações",
    "Fundos Imobiliários", "Reserva de Emergência", "Outros",
]

# ---------------------------------------------------------------------------
# Utilitários de calendário
# ---------------------------------------------------------------------------
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março",    4: "Abril",
    5: "Maio",    6: "Junho",     7: "Julho",     8: "Agosto",
    9: "Setembro",10: "Outubro",  11: "Novembro", 12: "Dezembro",
}
