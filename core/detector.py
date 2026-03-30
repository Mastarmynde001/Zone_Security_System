# Zone Security System - Detector Module
import cv2
from ultralytics import YOLO

class SecurityDetector:
    def __init__(self, model_path="yolov8n.pt"):
        # Load the highly optimized Nano model
        print(f"Loading YOLO model: {model_path}...")
        self.model = YOLO(model_path)
        
        # We only care about detecting humans for this security system.
        # Class 0 in the COCO dataset is 'person'. 
        self.target_classes = [0] 

    def process_frame(self, frame):
        """
        Takes a raw video frame, runs detection + tracking, 
        and returns the data we need for spatial logic.
        """
        # Run the tracker on the frame
        # persist=True is the magic that keeps tracking IDs across frames
        # verbose=False stops it from spamming your terminal output
        results = self.model.track(
            frame, 
            persist=True, 
            classes=self.target_classes,
            tracker="bytetrack.yaml", 
            verbose=False
        )
        
        tracked_objects = []
        
        # Extract the bounding boxes and IDs if any are found
        if results[0].boxes is not None and results[0].boxes.id is not None:
            # Move the tensor data to the CPU and convert to standard numpy arrays
            boxes = results[0].boxes.xyxy.cpu().numpy() # [x1, y1, x2, y2] format
            track_ids = results[0].boxes.id.int().cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            
            for box, track_id, conf in zip(boxes, track_ids, confidences):
                tracked_objects.append({
                    "id": track_id,
                    "bbox": box, 
                    "conf": conf
                })
                
        # Return both the raw data dictionary and a pre-annotated frame for our UI
        return tracked_objects, results[0].plot()