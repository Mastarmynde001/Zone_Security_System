import cv2
from ultralytics import YOLO

class SecurityDetector:
    def __init__(self, model_path="yolov8n.pt"):
        print(f"Loading YOLO model: {model_path}...")
        self.model = YOLO(model_path)
        
        self.target_classes = [0] 

    def process_frame(self, frame):
        """
        Takes a raw video frame, runs detection + tracking, 
        and returns the data we need for spatial logic.
        """
        
        results = self.model.track(
            frame, 
            persist=True, 
            classes=self.target_classes,
            tracker="bytetrack.yaml", 
            verbose=False
        )
        
        tracked_objects = []
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
           
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            
            for box, track_id, conf in zip(boxes, track_ids, confidences):
                tracked_objects.append({
                    "id": track_id,
                    "bbox": box, 
                    "conf": conf
                })
                
        return tracked_objects, results[0].plot()
