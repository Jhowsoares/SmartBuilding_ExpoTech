import time
import requests

print("Scheduler de Auditoria inicializado.")
while True:
    try:
        # Apenas monitora o andamento do tempo para manter o processo ativo
        r = requests.get("http://clock:8000/tick", timeout=2).json()
        print(f"[SCHEDULER MONITOR] Ciclo ativo. Relógio global está no Tick: {r.get('tick')}")
    except Exception:
        print("[SCHEDULER MONITOR] Sincronizando com o serviço central de tempo...")
    time.sleep(5)
