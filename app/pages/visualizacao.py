"""
visualizacao.py
---------------
Painel de acompanhamento financeiro: visão geral e por usuário.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import date

from app.database import get_connection
from app.auth import get_all_users
from config import MESES_PT


# ---------------------------------------------------------------------------
# Helpers de calendário
# ---------------------------------------------------------------------------

def _mes_anterior(ano: int, mes: int) -> tuple[int, int]:
    return (ano - 1, 12) if mes == 1 else (ano, mes - 1)


def _n_meses_atras(ano: int, mes: int, n: int) -> tuple[int, int]:
    """Retorna (ano, mes) de n meses antes do mês dado."""
    total = ano * 12 + (mes - 1) - n
    return total // 12, total % 12 + 1


def _periodo(ano: int, mes: int) -> str:
    return f"{MESES_PT[mes][:3]}/{ano}"


def _periodo_row(row) -> str:
    return _periodo(row["ano"], row["mes"])


# ---------------------------------------------------------------------------
# Helpers de query
# ---------------------------------------------------------------------------

def _ph(ids: list[int]) -> str:
    return ",".join("?" * len(ids))


def _mes_ref(conn, all_ids: list[int]) -> tuple[int, int]:
    """Mês mais recente com dados em qualquer tabela."""
    ph = _ph(all_ids)
    candidates = []
    for table in ("salarios", "despesas", "investimentos"):
        r = conn.execute(
            f"SELECT MAX(ano*100+mes) FROM {table} WHERE user_id IN ({ph})",
            all_ids,
        ).fetchone()[0]
        if r:
            candidates.append(r)
    if not candidates:
        t = date.today()
        return t.year, t.month
    v = max(candidates)
    return v // 100, v % 100


def _get_salarios_periodo(conn, user_ids: list[int], ano_ini: int, mes_ini: int,
                          ano_fim: int, mes_fim: int) -> pd.DataFrame:
    ph = _ph(user_ids)
    return conn.execute(
        f"SELECT s.ano, s.mes, u.nome AS usuario, "
        f"(s.salario + s.alimentacao + s.transporte + s.ferias + s.renda_extra) AS total "
        f"FROM salarios s JOIN users u ON s.user_id = u.id "
        f"WHERE s.user_id IN ({ph}) "
        f"  AND (s.ano*100+s.mes) >= ? AND (s.ano*100+s.mes) <= ? "
        f"ORDER BY s.ano, s.mes",
        user_ids + [ano_ini * 100 + mes_ini, ano_fim * 100 + mes_fim],
    ).df()


def _get_despesas_periodo(conn, user_ids: list[int], ano_ini: int, mes_ini: int,
                          ano_fim: int, mes_fim: int) -> pd.DataFrame:
    ph = _ph(user_ids)
    return conn.execute(
        f"SELECT d.ano, d.mes, u.nome AS usuario, d.categoria, d.valor "
        f"FROM despesas d JOIN users u ON d.user_id = u.id "
        f"WHERE d.user_id IN ({ph}) "
        f"  AND (d.ano*100+d.mes) >= ? AND (d.ano*100+d.mes) <= ? "
        f"ORDER BY d.ano, d.mes",
        user_ids + [ano_ini * 100 + mes_ini, ano_fim * 100 + mes_fim],
    ).df()


def _get_investimentos_periodo(conn, user_ids: list[int], ano_ini: int, mes_ini: int,
                               ano_fim: int, mes_fim: int) -> pd.DataFrame:
    ph = _ph(user_ids)
    return conn.execute(
        f"SELECT i.ano, i.mes, u.nome AS usuario, i.categoria, i.valor "
        f"FROM investimentos i JOIN users u ON i.user_id = u.id "
        f"WHERE i.user_id IN ({ph}) "
        f"  AND (i.ano*100+i.mes) >= ? AND (i.ano*100+i.mes) <= ? "
        f"ORDER BY i.ano, i.mes",
        user_ids + [ano_ini * 100 + mes_ini, ano_fim * 100 + mes_fim],
    ).df()


def _acumulado_inv_ate(conn, user_ids: list[int], ano: int, mes: int) -> float:
    ph = _ph(user_ids)
    r = conn.execute(
        f"SELECT COALESCE(SUM(valor), 0) FROM investimentos "
        f"WHERE user_id IN ({ph}) AND (ano*100+mes) <= ?",
        user_ids + [ano * 100 + mes],
    ).fetchone()[0]
    return float(r)


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

def _render_kpis(conn, user_ids: list[int], ano_ref: int, mes_ref: int) -> None:
    ano_ant, mes_ant = _mes_anterior(ano_ref, mes_ref)
    ano_12m, mes_12m = _n_meses_atras(ano_ref, mes_ref, 11)
    ph = _ph(user_ids)

    cutoff_ini = ano_12m * 100 + mes_12m
    cutoff_fim = ano_ref * 100 + mes_ref

    # --- Salário ---
    sal_atual = float(conn.execute(
        f"SELECT COALESCE(SUM(salario+alimentacao+transporte+ferias+renda_extra), 0) "
        f"FROM salarios WHERE user_id IN ({ph}) AND ano=? AND mes=?",
        user_ids + [ano_ref, mes_ref],
    ).fetchone()[0])

    sal_ant = float(conn.execute(
        f"SELECT COALESCE(SUM(salario+alimentacao+transporte+ferias+renda_extra), 0) "
        f"FROM salarios WHERE user_id IN ({ph}) AND ano=? AND mes=?",
        user_ids + [ano_ant, mes_ant],
    ).fetchone()[0])

    sal_media = float(conn.execute(
        f"SELECT COALESCE(AVG(total), 0) FROM ("
        f"  SELECT SUM(salario+alimentacao+transporte+ferias+renda_extra) AS total "
        f"  FROM salarios WHERE user_id IN ({ph}) "
        f"  AND (ano*100+mes) >= ? AND (ano*100+mes) <= ? "
        f"  GROUP BY ano, mes"
        f")",
        user_ids + [cutoff_ini, cutoff_fim],
    ).fetchone()[0])

    # --- Despesas ---
    desp_atual = float(conn.execute(
        f"SELECT COALESCE(SUM(valor), 0) FROM despesas "
        f"WHERE user_id IN ({ph}) AND ano=? AND mes=?",
        user_ids + [ano_ref, mes_ref],
    ).fetchone()[0])

    desp_ant = float(conn.execute(
        f"SELECT COALESCE(SUM(valor), 0) FROM despesas "
        f"WHERE user_id IN ({ph}) AND ano=? AND mes=?",
        user_ids + [ano_ant, mes_ant],
    ).fetchone()[0])

    desp_media = float(conn.execute(
        f"SELECT COALESCE(AVG(total), 0) FROM ("
        f"  SELECT SUM(valor) AS total "
        f"  FROM despesas WHERE user_id IN ({ph}) "
        f"  AND (ano*100+mes) >= ? AND (ano*100+mes) <= ? "
        f"  GROUP BY ano, mes"
        f")",
        user_ids + [cutoff_ini, cutoff_fim],
    ).fetchone()[0])

    # --- Saldo ---
    sal_12m = float(conn.execute(
        f"SELECT COALESCE(SUM(salario+alimentacao+transporte+ferias+renda_extra), 0) "
        f"FROM salarios WHERE user_id IN ({ph}) "
        f"AND (ano*100+mes) >= ? AND (ano*100+mes) <= ?",
        user_ids + [cutoff_ini, cutoff_fim],
    ).fetchone()[0])

    desp_12m = float(conn.execute(
        f"SELECT COALESCE(SUM(valor), 0) FROM despesas "
        f"WHERE user_id IN ({ph}) "
        f"AND (ano*100+mes) >= ? AND (ano*100+mes) <= ?",
        user_ids + [cutoff_ini, cutoff_fim],
    ).fetchone()[0])

    saldo_atual = sal_atual - desp_atual
    saldo_12m   = sal_12m - desp_12m

    # --- Investimentos ---
    inv_atual = float(conn.execute(
        f"SELECT COALESCE(SUM(valor), 0) FROM investimentos "
        f"WHERE user_id IN ({ph}) AND ano=? AND mes=?",
        user_ids + [ano_ref, mes_ref],
    ).fetchone()[0])

    inv_acum_total = _acumulado_inv_ate(conn, user_ids, ano_ref, mes_ref)
    inv_acum_ant   = _acumulado_inv_ate(conn, user_ids, ano_ant, mes_ant)

    # --- Delta ---
    def _delta(atual: float, anterior: float):
        if not anterior:
            return None
        return round((atual - anterior) / anterior * 100, 1)

    sal_delta  = _delta(sal_atual, sal_ant)
    desp_delta = _delta(desp_atual, desp_ant)
    inv_delta  = _delta(inv_atual, inv_acum_ant)

    def _fmt(v: float) -> str:
        return f"R$ {v:,.2f}"

    def _delta_str(d) -> str | None:
        return f"{d:+.1f}%" if d is not None else None

    def _metric_colorido(container, label: str, value: float) -> None:
        cor = "#28a745" if value >= 0 else "#dc3545"
        container.markdown(
            f"<p style='font-size:0.875rem;margin-bottom:0.25rem;color:rgba(49,51,63,0.6)'>{label}</p>"
            f"<p style='font-size:1.75rem;font-weight:700;margin:0;color:{cor}'>{_fmt(value)}</p>",
            unsafe_allow_html=True,
        )

    label_mes = f"{MESES_PT[mes_ref]}/{ano_ref}"

    rows = [
        (f"Salário — {label_mes}",       sal_atual,    sal_delta,  "Média últimos 12 meses", sal_media),
        (f"Despesas — {label_mes}",      desp_atual,   desp_delta, "Média últimos 12 meses", desp_media),
    ]

    for titulo, valor, delta, lbl2, val2 in rows:
        c1, c2 = st.columns(2)
        c1.metric(titulo, _fmt(valor), delta=_delta_str(delta))
        c2.metric(lbl2, _fmt(val2))

    c1, c2 = st.columns(2)
    _metric_colorido(c1, f"Saldo — {label_mes}", saldo_atual)
    _metric_colorido(c2, "Saldo últimos 12 meses", saldo_12m)

    c1, c2 = st.columns(2)
    c1.metric(f"Investimentos — {label_mes}", _fmt(inv_atual), delta=_delta_str(inv_delta))
    c2.metric("Total acumulado", _fmt(inv_acum_total))


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def _chart_salario_linha(df: pd.DataFrame, key: str) -> None:
    if df.empty:
        st.info("Sem dados de salário nos últimos 12 meses.")
        return
    df = df.copy()
    df["periodo"] = df.apply(_periodo_row, axis=1)
    evo = (
        df.groupby(["ano", "mes", "periodo", "usuario"])["total"]
        .sum().reset_index().sort_values(["ano", "mes"])
    )
    fig = px.line(
        evo, x="periodo", y="total", color="usuario", markers=True,
        labels={"periodo": "", "total": "Salário (R$)", "usuario": "Usuário"},
        title="Evolução do Salário — últimos 12 meses",
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True, key=key)


def _chart_despesas_linha(df: pd.DataFrame, key: str) -> None:
    if df.empty:
        st.info("Sem dados de despesas nos últimos 12 meses.")
        return
    df = df.copy()
    df["periodo"] = df.apply(_periodo_row, axis=1)
    evo = (
        df.groupby(["ano", "mes", "periodo"])["valor"]
        .sum().reset_index().sort_values(["ano", "mes"])
    )
    fig = px.line(
        evo, x="periodo", y="valor", markers=True,
        labels={"periodo": "", "valor": "Total (R$)"},
        title="Evolução das Despesas — últimos 12 meses",
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True, key=key)


def _chart_despesas_barra_mes(conn, user_ids: list[int],
                               ano_ref: int, mes_ref: int, key: str) -> None:
    ph = _ph(user_ids)
    df = conn.execute(
        f"SELECT categoria, SUM(valor) AS valor FROM despesas "
        f"WHERE user_id IN ({ph}) AND ano=? AND mes=? "
        f"GROUP BY categoria ORDER BY valor DESC",
        user_ids + [ano_ref, mes_ref],
    ).df()
    if df.empty:
        st.info(f"Sem despesas em {MESES_PT[mes_ref]}/{ano_ref}.")
        return
    fig = px.bar(
        df, x="categoria", y="valor", text_auto=".2s",
        labels={"categoria": "", "valor": "Valor (R$)"},
        title=f"Despesas por Categoria — {MESES_PT[mes_ref]}/{ano_ref}",
    )
    fig.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True, key=key)


def _chart_investimentos_linha(df: pd.DataFrame, prefix: str) -> None:
    if df.empty:
        st.info("Sem dados de investimentos nos últimos 12 meses.")
        return
    df = df.copy()

    cats = sorted(df["categoria"].unique().tolist())
    escolha = st.selectbox(
        "Filtrar por categoria:", ["Todas"] + cats, key=f"{prefix}_inv_cat"
    )
    if escolha != "Todas":
        df = df[df["categoria"] == escolha]

    df["periodo"] = df.apply(_periodo_row, axis=1)
    evo = (
        df.groupby(["ano", "mes", "periodo", "usuario"])["valor"]
        .sum().reset_index().sort_values(["ano", "mes"])
    )
    fig = px.line(
        evo, x="periodo", y="valor", color="usuario", markers=True,
        labels={"periodo": "", "valor": "Valor Aportado (R$)", "usuario": "Usuário"},
        title="Evolução dos Investimentos — últimos 12 meses",
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_inv_line")


# ---------------------------------------------------------------------------
# Seção completa (KPIs + 4 gráficos)
# ---------------------------------------------------------------------------

def _render_secao(conn, user_ids: list[int], ano_ref: int, mes_ref: int,
                  prefix: str) -> None:
    ano_12m, mes_12m = _n_meses_atras(ano_ref, mes_ref, 11)

    _render_kpis(conn, user_ids, ano_ref, mes_ref)

    st.markdown("")

    df_sal  = _get_salarios_periodo(conn, user_ids, ano_12m, mes_12m, ano_ref, mes_ref)
    df_desp = _get_despesas_periodo(conn, user_ids, ano_12m, mes_12m, ano_ref, mes_ref)
    df_inv  = _get_investimentos_periodo(conn, user_ids, ano_12m, mes_12m, ano_ref, mes_ref)

    col1, col2 = st.columns(2)
    with col1:
        _chart_salario_linha(df_sal, key=f"{prefix}_sal_line")
    with col2:
        _chart_despesas_linha(df_desp, key=f"{prefix}_desp_line")

    col3, col4 = st.columns(2)
    with col3:
        _chart_despesas_barra_mes(conn, user_ids, ano_ref, mes_ref, key=f"{prefix}_desp_bar")
    with col4:
        _chart_investimentos_linha(df_inv, prefix=prefix)


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------

def render_visualizacao() -> None:
    st.title("Painel Financeiro")
    conn = get_connection()

    usuarios = get_all_users()
    nomes = [u["nome"] for u in usuarios]
    ids   = [u["id"]   for u in usuarios]

    ano_ref, mes_ref = _mes_ref(conn, ids)

    # -- Visão Geral ----------------------------------------------------------
    st.header("Visão Geral")
    _render_secao(conn, ids, ano_ref, mes_ref, prefix="geral")

