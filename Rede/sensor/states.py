class SensorStateMachine:
    def __init__(self):
        self._estado = "ON"

    def atual(self):
        return self._estado

    def ativar(self):
        self._estado = "ON"

    def desativar(self):
        self._estado = "OFF"
