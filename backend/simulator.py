# simulator.py
"""
Rotate each coach's current image every `interval_seconds` seconds.
Updates state.json in place. Use --interval to change interval (seconds).
"""

import time, json, argparse, datetime, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
STATE_FILE = BASE_DIR / "data" / "state.json"
RESULTS_JSON = BASE_DIR / "data" / "results.json"

def classify_count(c, empty_max=3, moderate_max=7):
    if c <= empty_max:
        return "empty"
    if c <= moderate_max:
        return "moderate"
    return "crowded"

def load_results():
    with open(RESULTS_JSON, "r") as f:
        return json.load(f)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    state["generated_at"] = datetime.datetime.utcnow().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def rotate_once(state, results):
    # for each coach, advance current_index and update info
    for train in state["trains"]:
        for coach in train["coaches"]:
            pool = coach.get("pool", [])
            if not pool:
                continue
            # advance index cyclically
            idx = coach.get("current_index", 0)
            idx = (idx + 1) % len(pool)
            coach["current_index"] = idx
            img = pool[idx]
            coach["current_image"] = img
            # get count from results.json if available, else set 0
            count = int(results.get(img, {}).get("count", 0))
            coach["count"] = count
            coach["level"] = classify_count(count, coach.get("empty_max",3), coach.get("moderate_max",7))
            capacity = coach.get("capacity", 30) or 30
            coach["occupancy_percent"] = min(100, round((count / capacity) * 100))
            coach["last_updated"] = datetime.datetime.utcnow().isoformat()
    return state

def run_loop(interval_seconds=240, rounds=None):
    results = load_results()
    print(f"Loaded results.json with {len(results)} entries.")
    state = load_state()
    print("Starting simulator. Press Ctrl+C to stop.")
    i = 0
    try:
        while True:
            i += 1
            state = rotate_once(state, results)
            save_state(state)
            print(f"[{i}] Rotated all coaches at {datetime.datetime.utcnow().isoformat()} — saved state.json")
            if rounds and i >= rounds:
                print("Completed requested rounds. Exiting.")
                break
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Simulator stopped by user.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=int, default=240, help="Rotation interval in seconds (default 240 = 4 minutes)")
    p.add_argument("--rounds", type=int, default=None, help="Optional: run only N rotations then exit (for testing)")
    args = p.parse_args()
    run_loop(interval_seconds=args.interval, rounds=args.rounds)