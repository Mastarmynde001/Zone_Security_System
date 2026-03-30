# Zone Security System - Spatial Logic Module
import time
from shapely.geometry import Polygon, box

class ZoneIntrusionLogic:
    def __init__(self, zone_coordinates, threshold_ms=3000):
        """
        Initializes the restricted zone and the time threshold.
        zone_coordinates: List of (x, y) tuples defining the polygon.
        """
        try:
            # Create a mathematical polygon from our coordinates
            self.restricted_zone = Polygon(zone_coordinates)
            if not self.restricted_zone.is_valid:
                print("WARNING [Spatial Logic]: Polygon is invalid (e.g., lines cross).")
        except Exception as e:
            print(f"CRITICAL [Spatial Logic]: Failed to create zone. Error: {e}")
            self.restricted_zone = None

        # Convert threshold to seconds for easier math with time.time()
        self.threshold_sec = threshold_ms / 1000.0 
        
        # State management: keeps track of {tracker_id: time_entered_zone}
        self.active_intrusions = {}

    def evaluate_frame(self, tracked_objects):
        """
        Checks all current tracked objects against the restricted zone.
        Returns a list of IDs that have triggered the alarm.
        """
        if self.restricted_zone is None:
            return [] # Fail-safe: if no zone exists, no alarms are triggered.

        triggered_alarms = []
        current_frame_ids = set()

        for obj in tracked_objects:
            # Safely extract data
            try:
                obj_id = obj.get("id")
                x1, y1, x2, y2 = obj.get("bbox")
                current_frame_ids.add(obj_id)
            except (KeyError, TypeError) as e:
                print(f"ERROR [Spatial Logic]: Malformed tracking data. {e}")
                continue

            try:
                # Convert the YOLO bounding box into a Shapely rectangle
                target_box = box(x1, y1, x2, y2)

                # The core spatial math: Does the target overlap with our zone?
                if self.restricted_zone.intersects(target_box):
                    
                    # If this is the first time we see them in the zone, start the timer
                    if obj_id not in self.active_intrusions:
                        self.active_intrusions[obj_id] = time.time()

                    # Calculate how long they have been inside
                    time_inside = time.time() - self.active_intrusions[obj_id]

                    # Trigger alarm if they exceed your 3000ms threshold
                    if time_inside >= self.threshold_sec:
                        triggered_alarms.append({
                            "id": obj_id,
                            "time_inside": round(time_inside, 2),
                            "bbox": (x1, y1, x2, y2)
                        })
                else:
                    # If they step OUT of the zone, reset their timer
                    if obj_id in self.active_intrusions:
                        del self.active_intrusions[obj_id]

            except Exception as e:
                print(f"ERROR [Spatial Logic]: Math failure on ID {obj_id}. {e}")

        # Cleanup: If an ID disappears from the camera entirely, remove their timer
        lost_ids = set(self.active_intrusions.keys()) - current_frame_ids
        for lost_id in lost_ids:
            del self.active_intrusions[lost_id]

        return triggered_alarms