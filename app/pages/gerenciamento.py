"""
gerenciamento.py
----------------
Gerenciamento de categorias de despesas.
"""

import streamlit as st

from app.database import get_connection


def _get_categorias() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT id, nome FROM categorias ORDER BY nome").fetchall()
    return [{"id": r[0], "nome": r[1]} for r in rows]


def _add_categoria(nome: str) -> tuple[bool, str]:
    nome = nome.strip()
    if not nome:
        return False, "Nome não pode ser vazio."
    conn = get_connection()
    existe = conn.execute(
        "SELECT 1 FROM categorias WHERE LOWER(nome) = LOWER(?)", [nome]
    ).fetchone()
    if existe:
        return False, f'Categoria "{nome}" já existe.'
    conn.execute("INSERT INTO categorias (nome) VALUES (?)", [nome])
    return True, f'Categoria "{nome}" adicionada.'


def _delete_categoria(cat_id: int) -> None:
    get_connection().execute("DELETE FROM categorias WHERE id = ?", [cat_id])


def render_gerenciamento() -> None:
    st.header("Gerenciamento de Categorias")

    # --- Adicionar ---
    st.subheader("Nova Categoria")
    with st.form("form_add_categoria", clear_on_submit=True):
        nova = st.text_input("Nome da categoria")
        btn_add = st.form_submit_button("Adicionar", type="primary")

    if btn_add:
        ok, msg = _add_categoria(nova)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("---")

    # --- Listar / Excluir ---
    st.subheader("Categorias Cadastradas")
    categorias = _get_categorias()

    if not categorias:
        st.info("Nenhuma categoria cadastrada.")
        return

    for cat in categorias:
        col_nome, col_btn = st.columns([5, 1])
        col_nome.write(cat["nome"])
        if col_btn.button("Excluir", key=f"del_{cat['id']}", type="secondary"):
            _delete_categoria(cat["id"])
            st.rerun()
