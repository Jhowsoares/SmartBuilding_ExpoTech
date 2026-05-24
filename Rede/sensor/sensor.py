import os
import random
import time
import requests

class SensorStateMachine:
    def __init__(self):
        self._estado = "ON"
    def atual(self): return self._estado

class Sensor:
    def __init__(self, tipo: str, intervalo: int):
        self.tipo = tipo
        self.intervalo = intervalo
        self.id = f"sensor-{tipo}-{random.randint(1000, 9999)}"
        self.state = SensorStateMachine()
        print(f"[{self.id}] Sensor ativo — tipo={self.tipo}, intervalo={self.intervalo}")

    def gerar_valor(self):
        if self.tipo == "temperature": return round(random.uniform(18.0, 28.0), 2)
        if self.tipo == "humidity": return round(random.uniform(30.0, 70.0), 2)
        if self.tipo == "presence": return random.choice([0, 1])
        return round(random.uniform(0.0, 100.0), 2)

    def enviar(self, valor, timestamp, tick):
        payload = {
            "sensor_id": self.id,
            "tipo": self.tipo,
            "valor": valor,
            "tick": tick,
            "timestamp": timestamp
        }
        try:
            requests.post("http://server:5000/data", json=payload, timeout=2)
            print(f"[{self.id}] POST /data bem-sucedido: {valor}")
        except Exception as e:
            print(f"[{self.id}] Falha ao enviar: {e}")

    def iniciar_simulacao(self):
        """Loop contínuo que consulta o relógio e transmite os dados."""
        ultimo_tick = -1
        while True:
            try:
                # Consulta o relógio central via HTTP
                r = requests.get("http://clock:8000/tick", timeout=2).json()
                tick_atual = r.get("tick", 0)
                timestamp = r.get("timestamp", "")

                # Só processa se o relógio mudou de tick e bate com o intervalo do sensor
                if tick_atual != ultimo_tick:
                    if tick_atual % self.intervalo == 0 and self.state.atual() == "ON":
                        valor = self.gerar_valor()
                        self.enviar(valor, timestamp, tick_atual)
                    ultimo_tick = tick_atual
            except Exception:
                print(f"[{self.id}] Aguardando serviço de clock ficar online...")
            
            time.sleep(0.5)

if __name__ == "__main__":
    tipo = os.getenv("SENSOR_TIPO", "generic")
    intervalo = int(os.getenv("SENSOR_INTERVALO", "5"))
    sensor = Sensor(tipo, intervalo)
    sensor.iniciar_simulacao()
