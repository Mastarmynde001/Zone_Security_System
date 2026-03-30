import cv2
import sys
import time
import numpy as np
from core.detector import SecurityDetector
from utils.async_logger import AsyncLogger
from utils.video_buffer import VideoBuffer
from core.spatial_logic import ZoneIntrusionLogic

def main():
    print("Booting up the Intelligent Security System...")
    
    # 1. Initialize Modules
    detector = SecurityDetector(model_path="yolov8n.pt")
    zone_points = [(150, 100), (490, 100), (550, 380), (90, 380)]
    spatial_logic = ZoneIntrusionLogic(zone_coordinates=zone_points, threshold_ms=3000)
    cv_zone_polygon = np.array(zone_points, np.int32).reshape((-1, 1, 2))
    
    event_logger = AsyncLogger()
    video_recorder = VideoBuffer(fps=20, buffer_seconds=5)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("CRITICAL ERROR: Could not establish a connection to the camera.")
        sys.exit(1)

  
    window_name = "Zone Security System - Live Feed"
    
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
    
    cv2.resizeWindow(window_name, 1280, 720)

    print("System Live. You can now resize, minimize, or maximize the window.")
    print("Press 'q' to exit.")

    logged_ids = set()
    fps_on_this_machine = 0
    start_time = time.time()
    frame_count = 0
      
    print("System Live. Press 'q' to exit.")

    while True:
        success, frame = cap.read()
        if not success: break

        # Background processes
        video_recorder.add_frame(frame)
        tracked_objects, annotated_frame = detector.process_frame(frame)
        alarms = spatial_logic.evaluate_frame(tracked_objects)
        current_alarm_ids = {alarm['id'] for alarm in alarms}
        
        # --- UI & LOGGING ---
        zone_color = (0, 255, 0) # Green
        if len(alarms) > 0:
            zone_color = (0, 0, 255) # Red
            cv2.putText(annotated_frame, "WARNING: RESTRICTED ZONE BREACH", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            
            for alarm in alarms:
                x1, y1, x2, y2 = map(int, alarm["bbox"])
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
                
                # Logging & Video Trigger
                if alarm['id'] not in logged_ids:
                    event_logger.log_intrusion(alarm, frame)
                    current_fps = max(1, fps_on_this_machine)
                    video_recorder.save_event_clip(alarm['id'], current_fps) 
                    logged_ids.add(alarm['id'])

        # FPS Tracking
        frame_count += 1
        if frame_count >= 30:
            end_time = time.time()
            fps_on_this_machine = frame_count / (end_time - start_time)
            frame_count = 0
            start_time = time.time()

        # Clean up IDs and Draw Zone
        logged_ids.intersection_update(current_alarm_ids)
        cv2.polylines(annotated_frame, [cv_zone_polygon], isClosed=True, color=zone_color, thickness=2)
        
        # Show Frame
        cv2.imshow(window_name, annotated_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()