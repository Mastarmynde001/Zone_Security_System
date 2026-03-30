# 🛡️ Edge-Optimized Intelligent Security System

![System Demo](demo.gif)

> A real-time, event-driven security system that uses **YOLOv8 object detection**, **spatial geofencing**, and **asynchronous evidence capture** — engineered to run efficiently on CPU hardware.

---

## 1. The Problem

Traditional surveillance systems are fundamentally broken:

- **Storage waste** — They record 24/7, burning through **Terabytes** of storage to capture hours of empty hallways.
- **GPU dependency** — Most AI-powered alternatives require expensive dedicated GPUs, putting them out of reach for small deployments.
- **Reactive, not proactive** — Standard CCTV only helps *after* an incident, offering no real-time spatial awareness.

### The Solution

This system flips the model. Instead of recording everything, it **watches intelligently**:

1.  A **YOLOv8 Nano** model detects and tracks humans in real-time via ByteTrack.
2.  A **Shapely polygon geofence** defines a restricted zone directly on the camera feed.
3.  A **temporal threshold** (default: 3 seconds) filters out transient passers-by — an alarm only triggers if a person *lingers*.
4.  Evidence (cropped JPEG, CSV log, 5-second video clip) is captured **asynchronously**, so disk I/O never drops a single frame.

---

## 2. Key Architectural Decisions

### ⚡ Asynchronous Threading (Producer-Consumer Pattern)

Disk I/O is the #1 killer of real-time pipelines. Writing a JPEG to disk can take 15-30ms — enough to drop frames at 30 FPS. The `AsyncLogger` solves this with a **`queue.Queue` + `threading.Thread`** producer-consumer architecture. The main camera loop pushes tasks into the queue in **< 1ms** and never waits for the hard drive.

### 🎞️ Rolling Video Buffer (Circular RAM Buffer)

Pre-event context is critical for security footage ("*what happened 5 seconds before the alarm?*"). The `VideoBuffer` uses a `collections.deque` with a fixed `maxlen` to maintain a **5-second rolling window** of raw frames entirely in RAM — zero disk writes until an event fires.

### 🎯 Temporal FPS Calibration

Recorded clips can play back at the wrong speed if the encoding FPS doesn't match reality. The main loop calculates **actual throughput** every 30 frames and passes this calibrated FPS value to `VideoBuffer.save_event_clip()`, ensuring playback speed is always 1:1 regardless of CPU load.

### 📐 Spatial Geometry Engine

Instead of simple bounding-box center-point checks (which miss partial intrusions), the system converts YOLO `[x1, y1, x2, y2]` boxes into **Shapely rectangles** and performs `intersects()` against the restricted polygon. This catches edge cases where a person's body partially overlaps the zone boundary.

---

## 3. Tech Stack

| Layer          | Technology                                      |
|----------------|--------------------------------------------------|
| **Detection**  | Ultralytics YOLOv8n + ByteTrack                 |
| **Vision**     | OpenCV (`cv2`) — camera I/O, drawing, encoding  |
| **Math**       | NumPy (frame arrays), Shapely (polygon geometry) |
| **Concurrency**| `threading` + `queue` (stdlib)                   |
| **Buffering**  | `collections.deque` (stdlib circular buffer)     |
| **Runtime**    | Python 3.11+                                     |
| **Environment**| `uv` — fast Rust-based dependency resolver       |

---

## 4. Project Structure

```
Zone_Security_System/
│
├── main.py                   # Entry point: camera loop, UI rendering, orchestration
├── requirements.txt          # Pinned dependencies
│
├── core/
│   ├── detector.py           # YOLOv8 + ByteTrack detection & tracking
│   └── spatial_logic.py      # Polygon geofencing & temporal threshold logic
│
├── utils/
│   ├── async_logger.py       # Threaded producer-consumer evidence logger
│   └── video_buffer.py       # RAM-based circular video buffer
│
└── output/
    ├── events.csv            # Timestamped intrusion log
    ├── crops/                # Auto-cropped intruder JPEGs
    └── clips/                # 5-second pre-event MP4 clips
```

---

## 5. How to Run

### Prerequisites

- Python 3.11+
- A connected webcam (USB or built-in)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Zone_Security_System.git
cd Zone_Security_System

# 2. Create a virtual environment with uv
uv venv

# 3. Activate the environment
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 4. Install dependencies
uv pip install -r requirements.txt

# 5. Launch the system
python main.py
```

### Controls

| Key | Action                  |
|-----|-------------------------|
| `q` | Gracefully shut down    |

---

## 6. Output Examples

When an intrusion is detected, the system automatically generates:

| Output            | Location            | Description                                    |
|-------------------|----------------------|------------------------------------------------|
| **CSV Log**       | `output/events.csv`  | Timestamp, intruder ID, duration, crop filename |
| **Cropped Image** | `output/crops/`      | Padded JPEG crop of the detected intruder       |
| **Video Clip**    | `output/clips/`      | 5-second MP4 of the moments leading to the event|

Sample CSV output:

```
Timestamp,Intruder_ID,Duration_Sec,Crop_Filename
20260328_212301_727,1,3.07,intruder_1_20260328_212301_727.jpg
20260328_212416_223,4,3.01,intruder_4_20260328_212416_223.jpg
20260328_214838_299,12,3.02,intruder_12_20260328_214838_299.jpg
```

---

## 7. Customization

### Adjusting the Restricted Zone

Edit the polygon coordinates in `main.py` to match your physical space:

```python
zone_points = [(150, 100), (490, 100), (550, 380), (90, 380)]
```

### Changing the Time Threshold

Modify the `threshold_ms` parameter (default: 3000ms):

```python
spatial_logic = ZoneIntrusionLogic(zone_coordinates=zone_points, threshold_ms=5000)
```

---

<p align="center">
  Built with 🧠 YOLOv8 · 📐 Shapely · 🎥 OpenCV
</p>
