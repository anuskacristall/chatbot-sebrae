import hashlib
import os
import secrets
import uuid

# Sessões ativas em memória (token -> username)
ACTIVE_SESSIONS = {}

def gerar_hash_senha(senha: str):
    """Gera um hash PBKDF2 seguro e um salt aleatório para a senha."""
    salt = secrets.token_hex(16)
    hash_senha = hashlib.pbkdf2_hmac(
        'sha256',
        senha.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hash_senha, salt

def verificar_senha(senha_fornecida: str, password_hash: str, salt: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    hash_calculado = hashlib.pbkdf2_hmac(
        'sha256',
        senha_fornecida.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hash_calculado == password_hash

def criar_sessao(username: str, role: str = 'admin') -> str:
    """Gera um token de sessão e registra em memória com a role."""
    token = str(uuid.uuid4())
    ACTIVE_SESSIONS[token] = {"username": username, "role": role}
    return token

def verificar_sessao(token: str, required_role: str = None) -> bool:
    """Verifica se o token de sessão é válido e se possui a role necessária."""
    if not token or token not in ACTIVE_SESSIONS:
        return False
    if required_role:
        return ACTIVE_SESSIONS[token].get("role") == required_role
    return True

def obter_username_sessao(token: str) -> str:
    """Retorna o username associado à sessão."""
    if token in ACTIVE_SESSIONS:
        return ACTIVE_SESSIONS[token]["username"]
    return None

def encerrar_sessao(token: str):
    """Remove a sessão do cache em memória."""
    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
