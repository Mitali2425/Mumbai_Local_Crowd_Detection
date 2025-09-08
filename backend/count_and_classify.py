from ultralytics import YOLO
import os, json

# 1. Load pretrained YOLO model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "detection", "yolov8n.pt")
model = YOLO(MODEL_PATH)

# 2. Folder with your images
source_folder = os.path.join(BASE_DIR, "datasets", "crowd_dataset", "images")

# 3. Thresholds (tune these as needed)
thresholds = {
    "empty": (0, 3),
    "moderate": (4, 7),
    "crowded": (8, 1000)
}

results_data = {}

# 4. Run YOLO on each image and count persons
for img_file in os.listdir(source_folder):
    if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    
    img_path = os.path.join(source_folder, img_file)
    results = model(img_path, verbose=False)
    
    # YOLO returns detections; filter only class=0 (person in COCO dataset)
    person_count = 0
    for r in results:
        boxes = r.boxes
        for box in boxes:
            if int(box.cls[0]) == 0:  # class 0 = person
                person_count += 1
    
    # Classify based on thresholds
    if thresholds["empty"][0] <= person_count <= thresholds["empty"][1]:
        label = "Empty"
    elif thresholds["moderate"][0] <= person_count <= thresholds["moderate"][1]:
        label = "Moderate"
    else:
        label = "Crowded"
    
    # Save results
    results_data[img_file] = {
        "count": person_count,
        "label": label
    }

# 5. Save all results to a JSON file
RESULTS_PATH = os.path.join(BASE_DIR, "data", "results.json")
with open(RESULTS_PATH, "w") as f:
    json.dump(results_data, f, indent=4)

print("✅ Done! Results saved to results.json")
