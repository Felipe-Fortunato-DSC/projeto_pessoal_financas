"""
auth.py
-------
Lógica de autenticação: login, troca de senha e roteamento de telas.
"""

import streamlit as st

from app.database import get_connection
from app.utils import hash_password


def get_all_users() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT id, nome FROM users ORDER BY nome").fetchall()
    return [{"id": r[0], "nome": r[1]} for r in rows]


def verify_login(user_id: int, senha: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT senha_hash FROM users WHERE id = ?", [user_id]
    ).fetchone()
    return row is not None and row[0] == hash_password(senha)


def change_password(user_id: int, senha_atual: str, nova_senha: str) -> tuple[bool, str]:
    if not verify_login(user_id, senha_atual):
        return False, "Senha atual incorreta."
    if len(nova_senha) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres."
    get_connection().execute(
        "UPDATE users SET senha_hash = ? WHERE id = ?",
        [hash_password(nova_senha), user_id],
    )
    return True, "Senha alterada com sucesso!"


# ---------------------------------------------------------------------------
# Tela de login
# ---------------------------------------------------------------------------

def login_page() -> None:
    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        st.markdown(
            "<h1 style='text-align:center; color:#1a1a2e;'>Gestão Financeira</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h4 style='text-align:center; color:#4a4a6a;'>Família Fortunato</h4>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        usuarios = get_all_users()
        nomes = [u["nome"] for u in usuarios]
        ids   = [u["id"]   for u in usuarios]

        with st.form("form_login", clear_on_submit=False):
            selected_nome = st.selectbox("Usuário", nomes, key="login_user")
            senha         = st.text_input("Senha", type="password", key="login_senha")
            btn_entrar    = st.form_submit_button("Entrar", type="primary",
                                                  use_container_width=True)

        if btn_entrar:
            user_id = ids[nomes.index(selected_nome)]
            if verify_login(user_id, senha):
                st.session_state.logged_in       = True
                st.session_state.user_id         = user_id
                st.session_state.user_nome       = selected_nome
                st.session_state.trocar_senha_modo = False
                st.rerun()
            else:
                st.error("Senha incorreta. Tente novamente.")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Alterar Senha", use_container_width=True):
            st.session_state.trocar_senha_modo = True
            st.rerun()


# ---------------------------------------------------------------------------
# Tela de alterar senha
# ---------------------------------------------------------------------------

def tela_alterar_senha() -> None:
    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        st.markdown(
            "<h2 style='text-align:center; color:#1a1a2e;'>Alterar Senha</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        usuarios = get_all_users()
        nomes = [u["nome"] for u in usuarios]
        ids   = [u["id"]   for u in usuarios]

        with st.form("form_alterar_senha", clear_on_submit=True):
            selected_nome = st.selectbox("Usuário", nomes)
            user_id       = ids[nomes.index(selected_nome)]
            senha_atual   = st.text_input("Senha atual",          type="password")
            nova_senha    = st.text_input("Nova senha",           type="password")
            confirma      = st.text_input("Confirmar nova senha", type="password")
            btn_alterar   = st.form_submit_button("Alterar Senha", type="primary",
                                                   use_container_width=True)

        if btn_alterar:
            if not senha_atual or not nova_senha:
                st.error("Preencha todos os campos.")
            elif nova_senha != confirma:
                st.error("As novas senhas não coincidem.")
            else:
                ok, msg = change_password(user_id, senha_atual, nova_senha)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Voltar ao Login", use_container_width=True):
            st.session_state.trocar_senha_modo = False
            st.rerun()
