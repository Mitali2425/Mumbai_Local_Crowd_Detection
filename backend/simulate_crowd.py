# simulate_crowd.py
import json
import random
import time
import os
import sys
import traceback

# --- CONFIG ---
NUM_TRAINS = 3
NUM_COACHES = 12
REFRESH_INTERVAL = 30  # seconds per update
COACH_CAPACITY = 70

# Dummy schedule (replace with real schedule later)
SCHEDULES = [
    {"time": "02:05 PM", "src": "Panvel", "dst": "CSMT", "line": "Harbour Line", "code": "98122"},
    {"time": "02:12 PM", "src": "Panvel", "dst": "Vadala", "line": "Harbour Line", "code": "98124"},
    {"time": "02:18 PM", "src": "Panvel", "dst": "CSMT", "line": "Harbour Line", "code": "98126"},
]

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(BASE_DIR, "results.json")        # YOLO results
TRAIN_DATA_PATH = os.path.join(BASE_DIR, "train_data.json")  # output JSON

# Load YOLO results (fail early with helpful message)
try:
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)
except FileNotFoundError:
    print(f"ERROR: results.json not found at: {RESULTS_PATH}", file=sys.stderr)
    print("Make sure you have run YOLO inference and results.json exists.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print("ERROR: Failed to read results.json:", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

# Extract counts per image
image_counts = {image: info.get("count", 0) for image, info in results.items()}

# --- FUNCTIONS ---
def classify_crowd(count):
    """Return crowd status based on count."""
    if count <= 3:
        return "Empty"
    elif count <= 7:
        return "Moderate"
    else:
        return "Crowded"

def get_train_data():
    """Generate simulated train data with coaches and crowd status."""
    train_data = []
    image_list = list(image_counts.keys()) or [None]

    for t in range(NUM_TRAINS):
        sched = SCHEDULES[t % len(SCHEDULES)]

        train = {
            "train_id": t + 1,
            "code": sched["code"],
            "time": sched["time"],
            "src": sched["src"],
            "dst": sched["dst"],
            "line": sched["line"],
            "coaches": []
        }

        for c in range(1, NUM_COACHES + 1):
            img = random.choice(image_list) if image_list[0] is not None else None
            count = image_counts.get(img, 0) if img is not None else 0
            status = classify_crowd(count)

            train["coaches"].append({
                "index": c,
                "image": img,
                "count": count,
                "status": status,
                "capacity": COACH_CAPACITY,
                "occupancy_percent": round((count / COACH_CAPACITY) * 100, 1) if COACH_CAPACITY else 0
            })

        train_data.append(train)

    return train_data

# --- MAIN LOOP ---
if __name__ == "__main__":
    print(f"Simulation started. Updating {TRAIN_DATA_PATH} every {REFRESH_INTERVAL} seconds...")
    try:
        while True:
            try:
                data = get_train_data()
                with open(TRAIN_DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                # This exact line is printed each cycle as you requested
                print("Updated train_data.json")

            except Exception:
                # Print error but keep looping so the simulator continues
                print("ERROR while generating/updating train_data.json:", file=sys.stderr)
                traceback.print_exc()

            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        # graceful exit on Ctrl+C
        print("\nSimulation stopped by user (KeyboardInterrupt).")
        sys.exit(0)
