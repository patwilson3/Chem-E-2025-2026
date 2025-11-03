import cv2
import numpy as np
from collections import deque
import time
import random
import math
#from picamera2 import Picamera2, Preview
#from libcamera import controls
import threading
import os


# Threading event
operation_active = threading.Event()
camera_lock = threading.Lock()  # Only allows one thread to access the camera

# Constants for frame center and offset
CENTER_X, CENTER_Y = 600 // 2, 500 // 2
OFFSET = 20  # Half of the side length of the 100x100 area

def random_donut_points(cx, cy, r_inner, r_outer, n_points=100, frame_shape=None):
    """
    Generate n_points uniformly distributed in a 'donut' between
    r_inner and r_outer from the center (cx, cy).
    """
    points = []
    h, w = frame_shape if frame_shape is not None else (None, None)
    for _ in range(n_points):
        # Pick a random radius between r_inner and r_outer
        r = random.uniform(r_inner, r_outer)
        # Pick a random angle in [0, 2π)
        theta = random.uniform(0, 2*math.pi)
        # Convert polar -> cartesian
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)

        if frame_shape is None or (0 <= x < w and 0 <= y < h):
            points.append((x, y))
    return points


def measure_color_change(frame, pixels):
    """Extract RGB values for specified pixels and return their average."""
    color_values = []
    for x, y in pixels:
        x = int(x)
        y = int(y)
        if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
            color_values.extend(frame[y, x])
    if not color_values:
        return 0
    return np.mean(color_values)

def initialize_video(video_path):
    """Initialize a VideoCapture object from the given path."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")
    print(f"[INFO] Successfully opened video: {video_path}")
    return cap

def capture_frame(cap):
    """Safely capture a single frame and return RGB grayscale version."""
    ret, frame = cap.read()
    if not ret or frame is None:
        print("[INFO] End of video or failed frame capture.")
        return None
    try:
        frame_bw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_rgb = cv2.cvtColor(frame_bw, cv2.COLOR_GRAY2RGB)
        return frame_rgb
    except Exception as e:
        print(f"[ERROR] Failed cvtColor: {e}")
        return None

def calculate_offset(temp_array):
    """Calculate baseline offset from mean of temp array."""
    base_val = np.mean(temp_array)
    return base_val - 60

def process_frame(cap, pixels_to_measure, temp_array, stdev_array, offset, frame_size, start_time):
    """Process one frame and check for stabilization."""
    frame_rgb = capture_frame(cap)
    if frame_rgb is None:
        return False  # End of video or capture failure

    mean_color_value = measure_color_change(frame_rgb, pixels_to_measure)
    temp_array.append(mean_color_value)

    if len(temp_array) == temp_array.maxlen:
        if frame_size == (temp_array.maxlen - 1):
            offset = calculate_offset(temp_array)

        adjusted_mean = np.mean(temp_array) - offset
        if adjusted_mean > 80:
            stdev = np.std(np.array(temp_array) - offset)
            stdev_array.append(stdev)

            if stdev < 1.5:
                elapsed_time = time.time() - start_time
                print(f"[RESULT] Reaction stabilized at frame {frame_size}")
                print(f"[RESULT] Elapsed time (assuming 30 fps): {frame_size/30} s")
                return False

    return True

def running_alg(video_path):
    """Run main algorithm on given video."""
    with camera_lock:
        cap = initialize_video(video_path)
        ret, frame = cap.read()
        h, w = frame.shape[:2]
        temp_array = deque(maxlen=500)
        stdev_array = []
        frame_size = 0
        offset = 0
        start_time = time.time()
        width, height = 640, 480  # Example image size
        cx, cy = width / 2, height / 2  # Assume pill is at center
        r_inner = 80   # Approx radius to exclude around pill
        r_outer = 200 

        pixels_to_measure = random_donut_points(cx, cy, r_inner, r_outer, n_points=100, frame_shape=(h, w))

        operation_active.set()

        try:
            while operation_active.is_set():
                if not process_frame(cap, pixels_to_measure, temp_array, stdev_array, offset, frame_size, start_time):
                    break
                frame_size += 1
        finally:
            cap.release()
            cv2.destroyAllWindows()
            operation_active.clear()
            print("[INFO] Processing complete.")