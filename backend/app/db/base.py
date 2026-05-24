"""
Base declarativa do SQLAlchemy 2.0.

Todos os modelos ORM herdam de `Base`.
Importar este módulo antes de criar o engine garante que os metadados
de tabela fiquem registrados corretamente para o Alembic.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base de todos os modelos ORM do projeto."""
    pass
