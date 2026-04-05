import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Diretórios
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_LOCAL_PATH = str(DATA_DIR / "financas.duckdb")

# ---------------------------------------------------------------------------
# Senha seed (lida do ambiente; Streamlit Cloud usa st.secrets via database.py)
# ---------------------------------------------------------------------------
SEED_PASSWORD = os.environ.get("SEED_PASSWORD", "")

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
# Calendário
# ---------------------------------------------------------------------------
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março",    4: "Abril",
    5: "Maio",    6: "Junho",     7: "Julho",     8: "Agosto",
    9: "Setembro",10: "Outubro",  11: "Novembro", 12: "Dezembro",
}
