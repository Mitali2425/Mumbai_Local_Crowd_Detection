from ultralytics import YOLO
import os

# Load your YOLOv8 model
# model = YOLO("yolov8n.pt")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "detection", "yolov8n.pt")
model = YOLO(MODEL_PATH)   # or yolov8s.pt / yolov8m.pt depending on what you used

# Input folder with your dataset images
input_folder = os.path.join(BASE_DIR, "datasets", "crowd_dataset", "images")
# Output folder for annotated images
output_folder = os.path.join(BASE_DIR, "data", "annotated_results")
os.makedirs(output_folder, exist_ok=True)

# Run inference on all images in dataset
results = model.predict(
    source=input_folder,
    save=True,               # saves annotated images automatically
    project=output_folder,   # output directory
    name="runs",             # subfolder name
    conf=0.25                # confidence threshold (adjust if needed)
)

print("Annotated images saved in:", os.path.join(output_folder, "runs"))