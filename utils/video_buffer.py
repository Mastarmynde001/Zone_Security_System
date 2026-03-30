# Zone Security System - Video Buffer Utility
import cv2
import os
import threading
from collections import deque
from datetime import datetime

class VideoBuffer:
    def __init__(self, fps=20, buffer_seconds=5, output_dir="output/clips"):
        self.fps = fps
        self.buffer_seconds = buffer_seconds
        self.maxlen = fps * buffer_seconds
        self.frame_buffer = deque(maxlen=self.maxlen)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def add_frame(self, frame):
        """Continuously add frames to the rolling RAM buffer."""
        self.frame_buffer.append(frame.copy())

    def save_event_clip(self, intruder_id, actual_fps):
        threading.Thread(target=self._write_video, args=(intruder_id, actual_fps), daemon=True).start()

    def _write_video(self, intruder_id, actual_fps):
        if not self.frame_buffer:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"event_ID{intruder_id}_{timestamp}.mp4")
        
        # Get frame dimensions from the first frame in the buffer
        h, w = self.frame_buffer[0].shape[:2]
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, actual_fps, (w, h))

        # Copy the buffer to prevent 'deque mutated during iteration' errors
        frames_to_save = list(self.frame_buffer)

        for frame in frames_to_save:
            out.write(frame)
            
        out.release()
        print(f"[!] VIDEO SAVED: {filename}")