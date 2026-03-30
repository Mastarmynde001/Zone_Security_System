# Zone Security System - Async Logger Utility
import os
import cv2
import csv
from datetime import datetime
import threading
import queue

class AsyncLogger:
    def __init__(self, output_dir="output"):
        """Sets up the output folders, the CSV file, and starts the background worker."""
        self.output_dir = output_dir
        self.crops_dir = os.path.join(self.output_dir, "crops")
        self.csv_path = os.path.join(self.output_dir, "events.csv")
        
        # Build the folder structure if it doesn't exist yet
        os.makedirs(self.crops_dir, exist_ok=True)
        
        # Initialize the CSV with headers if we are starting fresh
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Intruder_ID", "Duration_Sec", "Crop_Filename"])

        # This Queue is the bridge between the fast camera loop and the slow hard drive
        self.log_queue = queue.Queue()
        
        # Spin up the background thread (daemon=True means it dies when the main program closes)
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def log_intrusion(self, alarm_data, raw_frame):
        """
        The main loop calls this. It instantly pushes the data into the queue 
        and returns control in less than a millisecond.
        """
        # CRITICAL: We use raw_frame.copy() so we are saving the clean image, 
        # not the one that already has red OpenCV rectangles drawn all over it.
        task = {
            'id': alarm_data['id'],
            'time_inside': alarm_data['time_inside'],
            'bbox': alarm_data['bbox'],
            'frame': raw_frame.copy() 
        }
        self.log_queue.put(task)

    def _process_queue(self):
        """The background worker loop. It waits for tasks and handles disk I/O."""
        while True:
            # This blocks and waits patiently until a task is in the queue
            task = self.log_queue.get()
            if task is None:
                break
                
            try:
                self._write_to_disk(task)
            except Exception as e:
                print(f"ERROR [AsyncLogger]: Disk write failed. {e}")
            finally:
                # Tell the queue we finished this specific job
                self.log_queue.task_done()

    def _write_to_disk(self, task):
        """The actual heavy lifting: cropping the image and saving the file."""
        # Generate a unique timestamp (e.g., 20260328_143022_125)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        target_id = task['id']
        frame = task['frame']
        
        # Extract bounding box
        x1, y1, x2, y2 = map(int, task['bbox'])
        h, w = frame.shape[:2]
        
        # Add 20 pixels of "padding" so the crop isn't suffocating their face
        pad = 20
        px1, py1 = max(0, x1 - pad), max(0, y1 - pad)
        px2, py2 = min(w, x2 + pad), min(h, y2 + pad)
        
        # Crop the array and save the JPEG
        crop = frame[py1:py2, px1:px2]
        crop_filename = f"intruder_{target_id}_{timestamp}.jpg"
        crop_path = os.path.join(self.crops_dir, crop_filename)
        cv2.imwrite(crop_path, crop)
        
        # Append the telemetry to the CSV database
        with open(self.csv_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, target_id, task['time_inside'], crop_filename])
            
        print(f"\n[+] LOGGED: Intruder {target_id} captured to {crop_filename}")