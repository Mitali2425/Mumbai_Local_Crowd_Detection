# server.py
from flask import Flask, jsonify, abort
import os, json

# serve static files from current directory (so /style.css and /script.js work)
app = Flask(__name__, static_folder=".", static_url_path="")

@app.route("/")
def index():
    return app.send_static_file("index.html")

# fallback for static files (CSS, JS, etc.)
@app.route("/<path:filename>")
def static_files(filename):
    if os.path.exists(filename):
        return app.send_static_file(filename)
    abort(404)

@app.route("/trains", methods=["GET"])
def get_trains():
    """
    Returns train list for frontend.
    - If train_data.json exists: return its data (array or mapping).
    - Else if state.json exists: return simplified train list.
    - Else: empty list.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TRAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "train_data.json")
    STATE_PATH = os.path.join(BASE_DIR, "data", "state.json")
    
    if os.path.exists(TRAIN_DATA_PATH):
        with open(TRAIN_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)

    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        trains = [
            {"train_id": t.get("train_id"), "code": t.get("code"), "line": t.get("line")}
            for t in state.get("trains", [])
        ]
        return jsonify(trains)

    return jsonify([])

@app.route("/train/<train_id>/status", methods=["GET"])
def get_train_status(train_id):
    """
    Fetch details for a specific train.
    - Supports both mapping ("Train1") and array (train_id/code) JSON formats.
    - Looks in train_data.json first, then state.json.
    """
    # ---- train_data.json first ----
    if os.path.exists(TRAIN_DATA_PATH):
        with open(TRAIN_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        train_info = None

        if isinstance(data, dict):
            # mapping style: { "Train1": {...}, "Train2": {...} }
            if train_id in data:
                train_info = data[train_id]
            else:
                # try case-insensitive match
                for k in data.keys():
                    if k.lower() == train_id.lower():
                        train_info = data[k]
                        break

        elif isinstance(data, list):
            # array style: [ { "train_id": 1, "code": "98122", ...}, ... ]
            for t in data:
                if str(t.get("train_id")) == str(train_id) or str(t.get("code")) == str(train_id):
                    train_info = t
                    break

        if not train_info:
            return jsonify({"error": f"Train {train_id} not found"}), 404

        return jsonify(train_info)

    # ---- fallback: state.json ----
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        for t in state.get("trains", []):
            if str(t.get("train_id")) == str(train_id) or str(t.get("code")) == str(train_id):
                return jsonify(t)
        return jsonify({"error": f"Train {train_id} not found"}), 404

    # nothing available
    return jsonify({"error": "No data files found (train_data.json or state.json)"}), 404


if __name__ == "__main__":
    # Run on 0.0.0.0 so LAN devices can also view it
    app.run(host="0.0.0.0", port=5000, debug=True)