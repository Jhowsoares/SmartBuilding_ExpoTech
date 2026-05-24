"""
Módulo: client
Descrição:
    Cliente simples que consulta periodicamente o servidor HTTP
    para obter os dados enviados pelos sensores simulados.
"""

import time
import requests


SERVER_URL = "http://server:5000/data"  # nome do serviço no docker-compose
INTERVALO = 2  # segundos entre consultas


def consultar_servidor():
    """
    Faz uma requisição GET ao servidor e retorna os dados.
    """
    try:
        resposta = requests.get(SERVER_URL, timeout=3)
        if resposta.status_code == 200:
            return resposta.json()
        else:
            return {"erro": f"Status inesperado: {resposta.status_code}"}
    except Exception as e:
        return {"erro": str(e)}


def main():
    print("Client iniciado. Consultando servidor periodicamente...\n")

    while True:
        dados = consultar_servidor()
        print("Dados recebidos:", dados)
        print("-" * 40)
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
