"""
carregar_dados.py
-----------------
Aba "Carregar Dados": inserção de salários e despesas mensais.
"""

import pandas as pd
import streamlit as st
from datetime import datetime

from app.database import get_connection
from app.auth import get_all_users
from config import MESES_PT, CATEGORIAS_INVESTIMENTOS

# Proporções das colunas da tabela de salários
_COLS_SAL = [0.6, 1.1, 1.5, 1.5, 1.5, 1.3, 1.5, 1.8, 0.45]
_HDRS_SAL = ["Ano", "Mês", "Salário", "Alimentação", "Transporte",
             "Férias", "Renda Extra", "Salário Final", ""]

# Proporções das colunas da tabela de despesas
_COLS_DESP = [0.6, 1.1, 1.5, 2.2, 1.5, 0.45]
_HDRS_DESP = ["Ano", "Mês", "Categoria", "Observação", "Valor", ""]

# Proporções das colunas da tabela de investimentos
_COLS_INV = [0.6, 1.1, 1.5, 1.0, 2.0, 1.5, 0.45]
_HDRS_INV = ["Ano", "Mês", "Categoria", "Origem", "Observação", "Valor", ""]

_ORIGENS_INVESTIMENTO = ["BRB", "XP", "Inter"]

PAGE_SIZE = 6


# ---------------------------------------------------------------------------
# Paginação
# ---------------------------------------------------------------------------

def _paginar(df: pd.DataFrame, page_key: str) -> tuple[pd.DataFrame, int, int, int]:
    """Calcula a fatia da página atual. Retorna (fatia, page, n_pages, total)."""
    total   = len(df)
    n_pages = max(1, -(-total // PAGE_SIZE))  # divisão com teto

    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    page = max(1, min(st.session_state[page_key], n_pages))
    st.session_state[page_key] = page

    start = (page - 1) * PAGE_SIZE
    return df.iloc[start : start + PAGE_SIZE], page, n_pages, total


def _nav_paginacao(page_key: str, page: int, n_pages: int, total: int) -> None:
    """Renderiza os controles de navegação abaixo da tabela."""
    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("← Anterior", key=f"{page_key}_prev", disabled=(page == 1)):
            st.session_state[page_key] -= 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<p style='text-align:center; margin:4px 0;'>"
            f"Página <b>{page}</b> de <b>{n_pages}</b>"
            f" &nbsp;|&nbsp; {total} registro(s)"
            f"</p>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Próxima →", key=f"{page_key}_next", disabled=(page == n_pages)):
            st.session_state[page_key] += 1
            st.rerun()


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def _get_categorias(conn) -> list[str]:
    rows = conn.execute("SELECT nome FROM categorias ORDER BY nome").fetchall()
    return [r[0] for r in rows]


def _get_salarios_usuario(conn, user_id: int) -> pd.DataFrame:
    return conn.execute(
        "SELECT id, ano, mes, salario, alimentacao, transporte, ferias, renda_extra "
        "FROM salarios WHERE user_id = ? ORDER BY ano DESC, mes DESC",
        [user_id],
    ).df()


def _get_investimentos_usuario(conn, user_id: int) -> pd.DataFrame:
    return conn.execute(
        "SELECT id, ano, mes, categoria, origem, observacao, valor "
        "FROM investimentos WHERE user_id = ? ORDER BY ano DESC, mes DESC",
        [user_id],
    ).df()


def _get_despesas(conn) -> pd.DataFrame:
    return conn.execute(
        "SELECT id, ano, mes, categoria, descricao, valor "
        "FROM despesas ORDER BY ano DESC, mes DESC"
    ).df()


# ---------------------------------------------------------------------------
# Dialogs de confirmação
# ---------------------------------------------------------------------------

@st.dialog("Confirmar exclusão")
def _dialog_excluir_salario(record_id: int, label: str) -> None:
    st.write(f"Excluir o registro de **{label}**?")
    st.write("Esta ação não pode ser desfeita.")
    c1, c2 = st.columns(2)
    if c1.button("Excluir", type="primary", use_container_width=True):
        get_connection().execute("DELETE FROM salarios WHERE id = ?", [record_id])
        st.rerun()
    if c2.button("Cancelar", use_container_width=True):
        st.rerun()


@st.dialog("Confirmar exclusão")
def _dialog_excluir_investimento(record_id: int, label: str) -> None:
    st.write(f"Excluir o investimento **{label}**?")
    st.write("Esta ação não pode ser desfeita.")
    c1, c2 = st.columns(2)
    if c1.button("Excluir", type="primary", use_container_width=True):
        get_connection().execute("DELETE FROM investimentos WHERE id = ?", [record_id])
        st.rerun()
    if c2.button("Cancelar", use_container_width=True):
        st.rerun()


@st.dialog("Confirmar exclusão")
def _dialog_excluir_despesa(record_id: int, label: str) -> None:
    st.write(f"Excluir a despesa **{label}**?")
    st.write("Esta ação não pode ser desfeita.")
    c1, c2 = st.columns(2)
    if c1.button("Excluir", type="primary", use_container_width=True):
        get_connection().execute("DELETE FROM despesas WHERE id = ?", [record_id])
        st.rerun()
    if c2.button("Cancelar", use_container_width=True):
        st.rerun()


# ---------------------------------------------------------------------------
# Renderizadores de tabela com X por linha
# ---------------------------------------------------------------------------

def _header_row(proporcoes: list, headers: list) -> None:
    """Linha de cabeçalho em negrito."""
    cols = st.columns(proporcoes)
    for col, h in zip(cols, headers):
        col.markdown(f"**{h}**")
    st.divider()


def _tabela_salarios(df: pd.DataFrame) -> None:
    fatia, page, n_pages, total = _paginar(df, "page_sal")
    _header_row(_COLS_SAL, _HDRS_SAL)

    for row in fatia.itertuples():
        total_sal = row.salario + row.alimentacao + row.transporte + row.ferias + row.renda_extra
        mes_nome  = MESES_PT[row.mes]
        label     = f"{mes_nome}/{row.ano}"

        cols = st.columns(_COLS_SAL)
        cols[0].write(str(row.ano))
        cols[1].write(mes_nome)
        cols[2].write(f"R$ {row.salario:,.2f}")
        cols[3].write(f"R$ {row.alimentacao:,.2f}")
        cols[4].write(f"R$ {row.transporte:,.2f}")
        cols[5].write(f"R$ {row.ferias:,.2f}")
        cols[6].write(f"R$ {row.renda_extra:,.2f}")
        cols[7].write(f"R$ {total_sal:,.2f}")
        if cols[8].button("✕", key=f"del_sal_{row.id}", help="Excluir registro"):
            _dialog_excluir_salario(row.id, label)

    _nav_paginacao("page_sal", page, n_pages, total)


def _tabela_investimentos(df: pd.DataFrame) -> None:
    fatia, page, n_pages, total = _paginar(df, "page_inv")
    _header_row(_COLS_INV, _HDRS_INV)

    for row in fatia.itertuples():
        mes_nome = MESES_PT[row.mes]
        label    = f"{row.categoria} | {mes_nome}/{row.ano}"
        obs      = row.observacao if row.observacao else "—"
        origem   = row.origem if row.origem else "—"

        cols = st.columns(_COLS_INV)
        cols[0].write(str(row.ano))
        cols[1].write(mes_nome)
        cols[2].write(row.categoria)
        cols[3].write(origem)
        cols[4].write(obs)
        cols[5].write(f"R$ {row.valor:,.2f}")
        if cols[6].button("✕", key=f"del_inv_{row.id}", help="Excluir registro"):
            _dialog_excluir_investimento(row.id, label)

    _nav_paginacao("page_inv", page, n_pages, total)


def _tabela_despesas(df: pd.DataFrame) -> None:
    fatia, page, n_pages, total = _paginar(df, "page_desp")
    _header_row(_COLS_DESP, _HDRS_DESP)

    for row in fatia.itertuples():
        mes_nome = MESES_PT[row.mes]
        label    = f"{row.categoria} | {mes_nome}/{row.ano}"
        obs      = row.descricao if row.descricao else "—"

        cols = st.columns(_COLS_DESP)
        cols[0].write(str(row.ano))
        cols[1].write(mes_nome)
        cols[2].write(row.categoria)
        cols[3].write(obs)
        cols[4].write(f"R$ {row.valor:,.2f}")
        if cols[5].button("✕", key=f"del_desp_{row.id}", help="Excluir registro"):
            _dialog_excluir_despesa(row.id, label)

    _nav_paginacao("page_desp", page, n_pages, total)


# ---------------------------------------------------------------------------
# Sub-aba: Salário
# ---------------------------------------------------------------------------

def _render_salario(conn) -> None:
    usuarios     = get_all_users()
    nomes        = [u["nome"] for u in usuarios]
    ids          = [u["id"]   for u in usuarios]
    hoje         = datetime.today()

    # Padrão: usuário logado
    default_idx  = nomes.index(st.session_state.user_nome) if st.session_state.user_nome in nomes else 0

    selected_nome = st.selectbox(
        "Usuário", nomes,
        index=default_idx,
        key="sal_user",
        label_visibility="collapsed",
    )
    user_id = ids[nomes.index(selected_nome)]

    # Reseta paginação ao trocar de usuário
    if st.session_state.get("sal_user_prev") != selected_nome:
        st.session_state["page_sal"] = 1
        st.session_state["sal_user_prev"] = selected_nome

    with st.expander("Inclusão de Salário"):
        with st.form("form_salario", clear_on_submit=True):
            col_esq, col_dir = st.columns(2)
            with col_esq:
                ano      = st.number_input("Ano", min_value=2020, max_value=2100,
                                           value=hoje.year, step=1)
                mes_nome = st.selectbox("Mês", list(MESES_PT.values()),
                                        index=hoje.month - 1)
                salario  = st.number_input("Salário (R$)",     min_value=0.0, format="%.2f")
                alim     = st.number_input("Alimentação (R$)", min_value=0.0, format="%.2f")
            with col_dir:
                transp      = st.number_input("Transporte (R$)", min_value=0.0, format="%.2f")
                ferias      = st.number_input("Férias (R$)",     min_value=0.0, format="%.2f")
                renda_extra = st.number_input("Renda Extra (R$)",min_value=0.0, format="%.2f")

            submitted = st.form_submit_button("Salvar", type="primary", use_container_width=True)

    if submitted:
        mes = [k for k, v in MESES_PT.items() if v == mes_nome][0]
        existe = conn.execute(
            "SELECT 1 FROM salarios WHERE user_id=? AND mes=? AND ano=?",
            [user_id, mes, ano],
        ).fetchone()
        if existe:
            st.warning(
                f"Já existe um registro de **{selected_nome}** para "
                f"**{mes_nome}/{ano}**. Exclua o registro abaixo antes de reinserir."
            )
        else:
            conn.execute(
                "INSERT INTO salarios "
                "(user_id, mes, ano, salario, alimentacao, transporte, ferias, renda_extra) "
                "VALUES (?,?,?,?,?,?,?,?)",
                [user_id, mes, ano, salario, alim, transp, ferias, renda_extra],
            )
            st.success(f"Salário de {selected_nome} em {mes_nome}/{ano} registrado!")
            st.rerun()

    # -- Tabela de registros -------------------------------------------------
    st.markdown(f"**{selected_nome}**")

    df = _get_salarios_usuario(conn, user_id)
    if df.empty:
        st.info("Nenhum registro encontrado.")
    else:
        _tabela_salarios(df)


# ---------------------------------------------------------------------------
# Sub-aba: Investimentos
# ---------------------------------------------------------------------------

def _render_investimentos(conn) -> None:
    usuarios    = get_all_users()
    nomes       = [u["nome"] for u in usuarios]
    ids         = [u["id"]   for u in usuarios]
    hoje        = datetime.today()
    default_idx = nomes.index(st.session_state.user_nome) if st.session_state.user_nome in nomes else 0

    selected_nome = st.selectbox(
        "Usuário", nomes,
        index=default_idx,
        key="inv_user",
        label_visibility="collapsed",
    )
    user_id = ids[nomes.index(selected_nome)]

    if st.session_state.get("inv_user_prev") != selected_nome:
        st.session_state["page_inv"] = 1
        st.session_state["inv_user_prev"] = selected_nome

    with st.expander("Inclusão de Investimento"):
        with st.form("form_investimento", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                ano       = st.number_input("Ano", min_value=2020, max_value=2100,
                                            value=hoje.year, step=1)
                mes_nome  = st.selectbox("Mês", list(MESES_PT.values()),
                                         index=hoje.month - 1)
                categoria = st.selectbox("Categoria", CATEGORIAS_INVESTIMENTOS)
                origem    = st.selectbox("Origem", _ORIGENS_INVESTIMENTO)
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
                obs   = st.text_input("Observação")

            submitted = st.form_submit_button("Salvar Investimento", type="primary",
                                              use_container_width=True)

    if submitted:
        mes = [k for k, v in MESES_PT.items() if v == mes_nome][0]
        conn.execute(
            "INSERT INTO investimentos (user_id, ano, mes, categoria, origem, valor, observacao) "
            "VALUES (?,?,?,?,?,?,?)",
            [user_id, ano, mes, categoria, origem, valor, obs or None],
        )
        st.success(f"Investimento de R$ {valor:,.2f} registrado!")
        st.rerun()

    with st.expander("Saque de Investimento"):
        with st.form("form_saque", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                ano_s      = st.number_input("Ano", min_value=2020, max_value=2100,
                                             value=hoje.year, step=1, key="saque_ano")
                mes_nome_s = st.selectbox("Mês", list(MESES_PT.values()),
                                          index=hoje.month - 1, key="saque_mes")
                categoria_s = st.selectbox("Categoria", CATEGORIAS_INVESTIMENTOS, key="saque_cat")
                origem_s    = st.selectbox("Origem", _ORIGENS_INVESTIMENTO, key="saque_orig")
            with col2:
                valor_s = st.number_input("Valor sacado (R$)", min_value=0.01, format="%.2f",
                                          key="saque_valor")
                obs_s   = st.text_input("Observação", key="saque_obs")

            btn_saque = st.form_submit_button("Registrar Saque", type="primary",
                                              use_container_width=True)

    if btn_saque:
        mes_s = [k for k, v in MESES_PT.items() if v == mes_nome_s][0]
        conn.execute(
            "INSERT INTO investimentos (user_id, ano, mes, categoria, origem, valor, observacao) "
            "VALUES (?,?,?,?,?,?,?)",
            [user_id, ano_s, mes_s, categoria_s, origem_s, -valor_s, obs_s or None],
        )
        st.success(f"Saque de R$ {valor_s:,.2f} registrado!")
        st.rerun()

    st.markdown(f"**{selected_nome}**")
    df = _get_investimentos_usuario(conn, user_id)
    if df.empty:
        st.info("Nenhum investimento registrado.")
    else:
        _tabela_investimentos(df)


# ---------------------------------------------------------------------------
# Sub-aba: Despesas
# ---------------------------------------------------------------------------

def _render_despesas(conn) -> None:
    categorias = _get_categorias(conn)
    hoje       = datetime.today()

    if not categorias:
        st.warning("Nenhuma categoria cadastrada.")
        return

    with st.expander("Inclusão de Despesas"):
        with st.form("form_despesa", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                ano       = st.number_input("Ano", min_value=2020, max_value=2100,
                                            value=hoje.year, step=1)
                mes_nome  = st.selectbox("Mês", list(MESES_PT.values()),
                                         index=hoje.month - 1)
                categoria = st.selectbox("Categoria", categorias)
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
                obs   = st.text_input("Observação")

            submitted = st.form_submit_button("Salvar Despesa", type="primary",
                                              use_container_width=True)

    if submitted:
        mes = [k for k, v in MESES_PT.items() if v == mes_nome][0]
        conn.execute(
            "INSERT INTO despesas (user_id, mes, ano, categoria, descricao, valor) "
            "VALUES (?,?,?,?,?,?)",
            [st.session_state.user_id, mes, ano, categoria, obs or None, valor],
        )
        st.success(f"Despesa de R$ {valor:,.2f} registrada!")
        st.rerun()

    # -- Tabela de registros -------------------------------------------------
    df = _get_despesas(conn)
    if df.empty:
        st.info("Nenhuma despesa registrada ainda.")
    else:
        _tabela_despesas(df)


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------

def render_carregar_dados() -> None:
    st.title("Carregar Dados")
    conn = get_connection()

    aba_sal, aba_desp, aba_inv = st.tabs(["Salário", "Despesas", "Investimentos"])

    with aba_sal:
        _render_salario(conn)

    with aba_desp:
        _render_despesas(conn)

    with aba_inv:
        _render_investimentos(conn)
