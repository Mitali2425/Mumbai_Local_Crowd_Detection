import json
import random
import os 
# Load YOLO results
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH = os.path.join(BASE_DIR, "data", "results.json")
with open(RESULTS_PATH, "r") as f:
    yolo_results = json.load(f)

# Classification thresholds
def classify(count):
    if count <= 3:
        return "Empty"
    elif count <= 7:
        return "Moderate"
    else:
        return "Crowded"

# Extract image counts from YOLO results
# Assuming results.json has format: {"image_path": {"person_count": N, ...}}
image_data = {img: data["count"] for img, data in yolo_results.items()}

# Simulate 3 trains with 12 coaches each
trains = {}
all_images = list(image_data.keys())

for t in range(1, 4):  # 3 trains
    coaches = {}
    for c in range(1, 13):  # 12 coaches
        img = random.choice(all_images)
        count = image_data[img]
        status = classify(count)
        coaches[f"Coach{c}"] = {"image": img, "count": count, "status": status}
    trains[f"Train{t}"] = {"coaches": coaches}

# Save the simulated train-coach mapping
TRAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "train_data.json")
with open(TRAIN_DATA_PATH, "w") as f:
    json.dump(trains, f, indent=4)

print("✅ Train data saved to train_data.json")