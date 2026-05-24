# server/server.py
"""
Server HTTP service.
Exposes:
 - POST /data  -> receives JSON payload from sensors, prints and stores it
 - GET  /data  -> returns list of received payloads (useful for client)
"""

from flask import Flask, request, jsonify
from datetime import datetime, timezone

app = Flask(__name__)
_received = []


@app.route("/data", methods=["POST"])
def receive_data():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    # attach server receive timestamp
    payload["_received_at"] = datetime.now(timezone.utc).isoformat()
    print("[SERVER] Received payload:", payload)
    _received.append(payload)

    # keep memory bounded (optional): keep last 1000 entries
    if len(_received) > 1000:
        _received.pop(0)

    return jsonify({"status": "ok"}), 201


@app.route("/data", methods=["GET"])
def list_data():
    # return a copy to avoid accidental mutation
    return jsonify(list(_received)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
