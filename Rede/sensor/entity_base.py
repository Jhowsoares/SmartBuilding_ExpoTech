"""
Módulo: entity_base
Descrição:
    Define a classe base para todas as entidades da simulação.
    Cada entidade possui:
        - ID automático
        - tipo (string livre)
        - estado ativo/inativo
        - método update(clock) obrigatório
"""

from abc import ABC, abstractmethod


class EntityBase(ABC):
    """
    Classe base para qualquer entidade da simulação.
    """

    _id_counter = 0  # contador global para IDs automáticos

    def __init__(self, tipo: str):
        if not tipo or not isinstance(tipo, str):
            raise ValueError("O tipo da entidade deve ser uma string não vazia.")

        EntityBase._id_counter += 1
        self.id = f"entity-{EntityBase._id_counter:03d}"
        self.tipo = tipo
        self.active = True

    # ------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------

    def activate(self) -> None:
        """Ativa a entidade."""
        self.active = True

    def deactivate(self) -> None:
        """Desativa a entidade."""
        self.active = False

    # ------------------------------------------------------------
    # Método obrigatório
    # ------------------------------------------------------------

    @abstractmethod
    def update(self, clock) -> None:
        """
        Método chamado pelo scheduler a cada tick.
        Deve ser implementado pelas subclasses.
        """
        pass

    # ------------------------------------------------------------
    # Representação
    # ------------------------------------------------------------

    def __repr__(self) -> str:
        estado = "ativo" if self.active else "inativo"
        return f"<{self.__class__.__name__} id={self.id} tipo={self.tipo} estado={estado}>"
