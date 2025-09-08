# create_mapping_and_state.py
"""
Create random mapping of images -> 3 trains x 12 coaches and generate state.json
Reads results.json for counts (falls back to computing with YOLO only if needed).
"""

import os, json, random, datetime
from pathlib import Path

# ===== CONFIG - change these if you want =====
BASE_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = BASE_DIR / "datasets" / "crowd_dataset" / "images"
RESULTS_JSON = BASE_DIR / "data" / "results.json"
OUT_STATE = BASE_DIR / "data" / "state.json"
NUM_TRAINS = 3
COACHES_PER_TRAIN = 12
POOL_SIZE_PER_COACH = 4   # how many different images each coach will cycle through (if available)
DEFAULT_EMPTY_MAX = 3
DEFAULT_MODERATE_MAX = 7
DEFAULT_CAPACITY = 30     # used to compute occupancy% (heuristic)
# =============================================

# Read results.json counts (must exist)
if not RESULTS_JSON.exists():
    raise SystemExit(f"Error: {RESULTS_JSON} not found. Run YOLO first to create results.json.")

with open(RESULTS_JSON, "r") as f:
    results = json.load(f)   # dict: image_name -> {"count": n, "level": "..."} or similar

# list images
images = sorted([p.name for p in IMAGES_DIR.iterdir() if p.suffix.lower() in (".jpg",".jpeg",".png")])
if not images:
    raise SystemExit(f"No images found inside {IMAGES_DIR}")

# helper classify function (consistent with your thresholds)
def classify_count(c, empty_max=DEFAULT_EMPTY_MAX, moderate_max=DEFAULT_MODERATE_MAX):
    if c <= empty_max:
        return "empty"
    if c <= moderate_max:
        return "moderate"
    return "crowded"

# pick images randomly for each coach
random.seed(42)  # for reproducibility; change or remove for new random assignments

state = {"generated_at": datetime.datetime.utcnow().isoformat(), "trains": []}
image_pool = images.copy()
# If you want to allow re-use we won't remove images; we'll pick random sample for each coach
for t in range(1, NUM_TRAINS + 1):
    train = {
        "train_id": t,
        "code": f"Train-{t} (Demo)",
        "line": "Dummy-Line",
        "coaches": []
    }
    for c in range(1, COACHES_PER_TRAIN + 1):
        # pick a pool of images for this coach (sample without replacement from images)
        pool = random.sample(images, min(POOL_SIZE_PER_COACH, len(images)))
        # choose initial current index 0 (will rotate through pool)
        current_index = 0
        current_image = pool[current_index]

        # get count from results.json if present; else default to 0 and level unknown
        count = int(results.get(current_image, {}).get("count", 0))
        level = classify_count(count)

        coach = {
            "coach_id": f"{t}-{c}",            # string id "train-coach"
            "train_id": t,
            "index": c,                        # 1..12
            "pool": pool,                      # list of image filenames assigned to this coach
            "current_index": current_index,    # index into pool
            "current_image": current_image,
            "count": count,
            "level": level,
            "empty_max": DEFAULT_EMPTY_MAX,
            "moderate_max": DEFAULT_MODERATE_MAX,
            "capacity": DEFAULT_CAPACITY,
            "occupancy_percent": min(100, round((count / DEFAULT_CAPACITY) * 100)),
            "last_updated": datetime.datetime.utcnow().isoformat()
        }
        train["coaches"].append(coach)
    state["trains"].append(train)

# Save state.json
with open(OUT_STATE, "w") as f:
    json.dump(state, f, indent=2)

print(f"Created {OUT_STATE} with {NUM_TRAINS} trains x {COACHES_PER_TRAIN} coaches.")
print("Open state.json to see structure.")