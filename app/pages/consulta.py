"""
consulta.py
-----------
Aba de consulta: visualização paginada de salários, despesas e investimentos.
"""

import pandas as pd
import streamlit as st

from app.database import get_connection
from app.auth import get_all_users
from config import MESES_PT

PAGE_SIZE = 12


# ---------------------------------------------------------------------------
# Helpers de paginação
# ---------------------------------------------------------------------------

def _paginar(df: pd.DataFrame, page_key: str) -> tuple[pd.DataFrame, int, int, int]:
    total   = len(df)
    n_pages = max(1, -(-total // PAGE_SIZE))
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    page = max(1, min(st.session_state[page_key], n_pages))
    st.session_state[page_key] = page
    start = (page - 1) * PAGE_SIZE
    return df.iloc[start:start + PAGE_SIZE], page, n_pages, total


def _nav(page_key: str, page: int, n_pages: int, total: int) -> None:
    col_prev, col_info, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("← Anterior", key=f"{page_key}_prev", disabled=(page == 1)):
            st.session_state[page_key] -= 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<p style='text-align:center;margin:4px 0'>"
            f"Página <b>{page}</b> de <b>{n_pages}</b> &nbsp;|&nbsp; {total} registro(s)"
            f"</p>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Próxima →", key=f"{page_key}_next", disabled=(page == n_pages)):
            st.session_state[page_key] += 1
            st.rerun()


def _reset_page_on_filter_change(page_key: str, filter_key: str, filter_val) -> None:
    if st.session_state.get(filter_key) != filter_val:
        st.session_state[page_key]  = 1
        st.session_state[filter_key] = filter_val


def _anos_disponiveis(conn, table: str) -> list[str]:
    rows = conn.execute(
        f"SELECT DISTINCT ano FROM {table} ORDER BY ano DESC"
    ).fetchall()
    return ["Todos"] + [str(r[0]) for r in rows]


def _meses_lista() -> list[str]:
    return ["Todos"] + list(MESES_PT.values())


# ---------------------------------------------------------------------------
# Sub-aba: Salários
# ---------------------------------------------------------------------------

def _render_consulta_salarios(conn) -> None:
    usuarios = get_all_users()
    nomes    = ["Todos"] + [u["nome"] for u in usuarios]
    ids      = {u["nome"]: u["id"] for u in usuarios}

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_usuario = st.selectbox("Usuário", nomes, key="csal_usuario")
    with col2:
        sel_mes_nome = st.selectbox("Mês", _meses_lista(), key="csal_mes")
    with col3:
        sel_ano_label = st.selectbox("Ano", _anos_disponiveis(conn, "salarios"), key="csal_ano")

    filtro = (sel_usuario, sel_mes_nome, sel_ano_label)
    _reset_page_on_filter_change("page_csal", "csal_filter", filtro)

    conditions, params = [], []
    if sel_usuario != "Todos":
        conditions.append("s.user_id = ?")
        params.append(ids[sel_usuario])
    if sel_mes_nome != "Todos":
        mes_num = next(k for k, v in MESES_PT.items() if v == sel_mes_nome)
        conditions.append("s.mes = ?")
        params.append(mes_num)
    if sel_ano_label != "Todos":
        conditions.append("s.ano = ?")
        params.append(int(sel_ano_label))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    df = conn.execute(
        f"SELECT u.nome AS Usuário, s.ano AS Ano, s.mes AS _mes, "
        f"s.salario AS Salário, s.alimentacao AS Alimentação, "
        f"s.transporte AS Transporte, s.ferias AS Férias, "
        f"s.renda_extra AS 'Renda Extra', "
        f"(s.salario+s.alimentacao+s.transporte+s.ferias+s.renda_extra) AS Total "
        f"FROM salarios s JOIN users u ON s.user_id = u.id {where} "
        f"ORDER BY s.ano DESC, s.mes DESC",
        params,
    ).df()

    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    df.insert(2, "Mês", df["_mes"].map(MESES_PT))
    df = df.drop(columns=["_mes"])

    fatia, page, n_pages, total = _paginar(df, "page_csal")
    st.dataframe(fatia, use_container_width=True, hide_index=True)
    _nav("page_csal", page, n_pages, total)


# ---------------------------------------------------------------------------
# Sub-aba: Despesas
# ---------------------------------------------------------------------------

def _render_consulta_despesas(conn) -> None:
    cats = ["Todas"] + [r[0] for r in conn.execute(
        "SELECT nome FROM categorias ORDER BY nome"
    ).fetchall()]

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_cat = st.selectbox("Categoria", cats, key="cdesp_cat")
    with col2:
        sel_mes_nome = st.selectbox("Mês", _meses_lista(), key="cdesp_mes")
    with col3:
        sel_ano_label = st.selectbox("Ano", _anos_disponiveis(conn, "despesas"), key="cdesp_ano")

    filtro = (sel_cat, sel_mes_nome, sel_ano_label)
    _reset_page_on_filter_change("page_cdesp", "cdesp_filter", filtro)

    conditions, params = [], []
    if sel_cat != "Todas":
        conditions.append("d.categoria = ?")
        params.append(sel_cat)
    if sel_mes_nome != "Todos":
        mes_num = next(k for k, v in MESES_PT.items() if v == sel_mes_nome)
        conditions.append("d.mes = ?")
        params.append(mes_num)
    if sel_ano_label != "Todos":
        conditions.append("d.ano = ?")
        params.append(int(sel_ano_label))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    df = conn.execute(
        f"SELECT d.ano AS Ano, d.mes AS _mes, d.categoria AS Categoria, "
        f"COALESCE(d.descricao, '') AS Observação, d.valor AS Valor "
        f"FROM despesas d {where} "
        f"ORDER BY d.ano DESC, d.mes DESC",
        params,
    ).df()

    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    df.insert(1, "Mês", df["_mes"].map(MESES_PT))
    df = df.drop(columns=["_mes"])

    fatia, page, n_pages, total = _paginar(df, "page_cdesp")
    st.dataframe(fatia, use_container_width=True, hide_index=True)
    _nav("page_cdesp", page, n_pages, total)


# ---------------------------------------------------------------------------
# Sub-aba: Investimentos
# ---------------------------------------------------------------------------

def _render_consulta_investimentos(conn) -> None:
    usuarios = get_all_users()
    nomes    = ["Todos"] + [u["nome"] for u in usuarios]
    ids      = {u["nome"]: u["id"] for u in usuarios}

    cats = ["Todas"] + [r[0] for r in conn.execute(
        "SELECT DISTINCT categoria FROM investimentos ORDER BY categoria"
    ).fetchall()]
    origens = ["Todas"] + [r[0] for r in conn.execute(
        "SELECT DISTINCT origem FROM investimentos WHERE origem IS NOT NULL ORDER BY origem"
    ).fetchall()]

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_usuario = st.selectbox("Usuário", nomes, key="cinv_usuario")
        sel_cat     = st.selectbox("Categoria", cats, key="cinv_cat")
    with col2:
        sel_origem    = st.selectbox("Origem", origens, key="cinv_origem")
        sel_mes_nome  = st.selectbox("Mês", _meses_lista(), key="cinv_mes")
    with col3:
        sel_ano_label = st.selectbox("Ano", _anos_disponiveis(conn, "investimentos"), key="cinv_ano")

    filtro = (sel_usuario, sel_cat, sel_origem, sel_mes_nome, sel_ano_label)
    _reset_page_on_filter_change("page_cinv", "cinv_filter", filtro)

    conditions, params = [], []
    if sel_usuario != "Todos":
        conditions.append("i.user_id = ?")
        params.append(ids[sel_usuario])
    if sel_cat != "Todas":
        conditions.append("i.categoria = ?")
        params.append(sel_cat)
    if sel_origem != "Todas":
        conditions.append("i.origem = ?")
        params.append(sel_origem)
    if sel_mes_nome != "Todos":
        mes_num = next(k for k, v in MESES_PT.items() if v == sel_mes_nome)
        conditions.append("i.mes = ?")
        params.append(mes_num)
    if sel_ano_label != "Todos":
        conditions.append("i.ano = ?")
        params.append(int(sel_ano_label))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    df = conn.execute(
        f"SELECT u.nome AS Usuário, i.ano AS Ano, i.mes AS _mes, "
        f"i.categoria AS Categoria, COALESCE(i.origem, '') AS Origem, "
        f"COALESCE(i.observacao, '') AS Observação, i.valor AS Valor, "
        f"COALESCE(i.tipo, 'entrada') AS _tipo "
        f"FROM investimentos i JOIN users u ON i.user_id = u.id {where} "
        f"ORDER BY i.ano DESC, i.mes DESC",
        params,
    ).df()

    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    df.insert(2, "Mês", df["_mes"].map(MESES_PT))
    df["Situação"] = df["_tipo"].map({"entrada": "Entrada", "saida": "Saída"})
    df = df.drop(columns=["_mes", "_tipo"])

    fatia, page, n_pages, total = _paginar(df, "page_cinv")
    st.dataframe(fatia, use_container_width=True, hide_index=True)
    _nav("page_cinv", page, n_pages, total)


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------

def render_consulta() -> None:
    st.title("Consulta")

    conn = get_connection()
    aba_sal, aba_desp, aba_inv = st.tabs(["Salários", "Despesas", "Investimentos"])

    with aba_sal:
        _render_consulta_salarios(conn)

    with aba_desp:
        _render_consulta_despesas(conn)

    with aba_inv:
        _render_consulta_investimentos(conn)
