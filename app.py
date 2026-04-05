"""
app.py
------
Ponto de entrada do aplicativo. Execute com:
    streamlit run app.py
"""

import streamlit as st

from app.auth import login_page, tela_alterar_senha
from app.pages.carregar_dados import render_carregar_dados
from app.pages.visualizacao import render_visualizacao
from config import USE_MOTHERDUCK, MOTHERDUCK_DB, DB_LOCAL_PATH

st.set_page_config(
    page_title="Gestão Financeira – Família Fortunato",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Estado de sessão
# ---------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in         = False
    st.session_state.user_id           = None
    st.session_state.user_nome         = None
    st.session_state.trocar_senha_modo = False

# ---------------------------------------------------------------------------
# Roteamento
# ---------------------------------------------------------------------------
if not st.session_state.logged_in:
    if st.session_state.trocar_senha_modo:
        tela_alterar_senha()
    else:
        login_page()
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar — boas-vindas, status de conexão e logout
# ---------------------------------------------------------------------------
primeiro_nome = st.session_state.user_nome.split()[0]
st.sidebar.markdown(f"### Olá, {primeiro_nome}!")
st.sidebar.markdown(f"*{st.session_state.user_nome}*")
st.sidebar.markdown("---")

if USE_MOTHERDUCK:
    st.sidebar.success(f"☁️ MotherDuck\n`{MOTHERDUCK_DB}`")
else:
    st.sidebar.info(f"🦆 DuckDB local\n`financas.duckdb`")

st.sidebar.markdown("---")

if st.sidebar.button("Sair", use_container_width=True):
    st.session_state.logged_in         = False
    st.session_state.user_id           = None
    st.session_state.user_nome         = None
    st.session_state.trocar_senha_modo = False
    st.rerun()

# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------
aba_painel, aba_dados = st.tabs(["Painel", "Carregar Dados"])

with aba_painel:
    render_visualizacao()

with aba_dados:
    render_carregar_dados()
