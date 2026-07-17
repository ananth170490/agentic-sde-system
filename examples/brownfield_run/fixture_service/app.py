from __future__ import annotations

from flask import Flask, jsonify, request

app = Flask(__name__)

NOTES: dict[int, dict[str, str]] = {
    1: {"title": "first", "content": "hello"},
}


@app.get("/notes")
def list_notes():
    return jsonify({"notes": [{"id": note_id, **note} for note_id, note in NOTES.items()]})


@app.post("/notes")
def create_note():
    payload = request.get_json(silent=True) or {}
    note_id = max(NOTES.keys(), default=0) + 1
    NOTES[note_id] = {
        "title": str(payload.get("title", "")),
        "content": str(payload.get("content", "")),
    }
    return jsonify({"id": note_id, **NOTES[note_id]}), 201


@app.put("/notes/<int:note_id>")
def update_note(note_id: int):
    if note_id not in NOTES:
        return jsonify({"error": "not found"}), 404

    payload = request.get_json(silent=True) or {}
    NOTES[note_id]["title"] = str(payload.get("title", NOTES[note_id]["title"]))
    NOTES[note_id]["content"] = str(payload.get("content", NOTES[note_id]["content"]))
    return jsonify({"id": note_id, **NOTES[note_id]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
