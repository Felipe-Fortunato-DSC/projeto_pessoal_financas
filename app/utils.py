"""
utils.py
--------
Funções utilitárias compartilhadas entre os módulos da aplicação.
"""

import hashlib


def hash_password(password: str) -> str:
    """Retorna o hash SHA-256 da senha fornecida."""
    return hashlib.sha256(password.encode()).hexdigest()
