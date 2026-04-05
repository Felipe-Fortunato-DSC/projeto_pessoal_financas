import os
from pathlib import Path

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
MOTHERDUCK_TOKEN = os.environ.get("MOTHERDUCK_TOKEN", "")
MOTHERDUCK_DB    = os.environ.get("MOTHERDUCK_DB", "financas")
USE_MOTHERDUCK   = bool(MOTHERDUCK_TOKEN)

# ---------------------------------------------------------------------------
# Usuários iniciais (seed)
# ---------------------------------------------------------------------------
USUARIOS_INICIAIS = [
    {"nome": "Monique Fortunato", "senha": "Moniqu&2019"},
    {"nome": "Felipe Fortunato",  "senha": "Moniqu&2019"},
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
