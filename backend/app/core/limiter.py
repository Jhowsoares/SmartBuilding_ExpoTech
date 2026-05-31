"""Instância global do rate limiter (slowapi).

Módulo isolado para evitar importação circular entre main.py e os routers.
Importar daqui em vez de app.main:

    from app.core.limiter import limiter
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)