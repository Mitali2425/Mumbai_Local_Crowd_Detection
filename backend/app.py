from flask import Flask, jsonify, send_from_directory
import json
import os

# backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# paths
DATA_PATH = os.path.join(BASE_DIR, "train_data.json")
FRONTEND_PATH = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path="")

@app.route("/trains")
def get_trains():
    """Return the full train list from train_data.json"""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/train/<train_id>/status")
def get_train_status(train_id):
    """Return details for a specific train from train_data.json"""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Case 1: JSON is mapping style { "Train1": {...}, "Train2": {...} }
    if isinstance(data, dict):
        if train_id in data:
            return jsonify(data[train_id])
        # fallback: case-insensitive match
        for k in data.keys():
            if k.lower() == train_id.lower():
                return jsonify(data[k])
        return jsonify({"error": "Train not found"}), 404

    # Case 2: JSON is array style [ {...}, {...} ]
    if isinstance(data, list):
        for t in data:
            if str(t.get("train_id")) == str(train_id) or str(t.get("code")) == str(train_id):
                return jsonify(t)
        return jsonify({"error": "Train not found"}), 404

    return jsonify({"error": "Invalid data format"}), 500

@app.route("/")
def index():
    """Serve the frontend index.html"""
    return send_from_directory(FRONTEND_PATH, "index.html")

if __name__ == "__main__":
    # run Flask server
    app.run(debug=True)
