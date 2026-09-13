from flask import Flask, request, jsonify
import json
import uuid
from pathlib import Path

app = Flask(__name__)
TICKETS_FILE = Path(__file__).parent / "tickets.json"


@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()
    ticket = {
        "ticket_id": str(uuid.uuid4())[:8],
        "issue": data.get("issue", ""),
        "urgency": data.get("urgency", "MEDIUM"),
    }

    tickets = []
    if TICKETS_FILE.exists():
        tickets = json.loads(TICKETS_FILE.read_text())
    tickets.append(ticket)
    TICKETS_FILE.write_text(json.dumps(tickets, indent=2))

    return jsonify({"status": "logged", "ticket": ticket})


@app.route("/tickets", methods=["GET"])
def list_tickets():
    if not TICKETS_FILE.exists():
        return jsonify([])
    return jsonify(json.loads(TICKETS_FILE.read_text()))


if __name__ == "__main__":
    app.run(port=5000, debug=True)