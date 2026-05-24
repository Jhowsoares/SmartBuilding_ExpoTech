# clock/clock.py
"""
Clock HTTP service.
Exposes GET /tick returning JSON: {"tick": <int>, "timestamp": "<ISO8601>"}
"""

from flask import Flask, jsonify
import threading
import time
from datetime import datetime, timezone

app = Flask(__name__)
_tick = 0
_tick_lock = threading.Lock()


def loop_clock():
    global _tick
    while True:
        with _tick_lock:
            _tick += 1
            current = _tick
        # advance once per second (accelerated clock can be tuned here)
        time.sleep(1)


@app.route("/tick", methods=["GET"])
def get_tick():
    with _tick_lock:
        current_tick = _tick
    iso_ts = datetime.now(timezone.utc).isoformat()
    return jsonify({"tick": current_tick, "timestamp": iso_ts})


if __name__ == "__main__":
    t = threading.Thread(target=loop_clock, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=8000)
