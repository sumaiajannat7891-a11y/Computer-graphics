# src/storage.py
import json
import os

DATA_FILE = "data/scores.json"

def load_game_data():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        default_data = {"high_score": 0, "unlocked_blades": ["Cyber Cyan"]}
        save_game_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"high_score": 0, "unlocked_blades": ["Cyber Cyan"]}

def save_game_data(data):
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_high_score():
    data = load_game_data()
    if isinstance(data, dict):
        return data.get("high_score", 0)
    return data or 0

def save_high_score(score):
    data = load_game_data()
    if isinstance(data, dict):
        data["high_score"] = max(score, data.get("high_score", 0))
        save_game_data(data)
    else:
        save_game_data({"high_score": score})
