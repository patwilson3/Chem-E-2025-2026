import os
import sys
import time
from datetime import datetime
from picamera2 import Picamera2
import sys
import time
from datetime import datetime
from picamera2 import Picamera2
from picamera2.outputs import FileOutput, FfmpegOutput
from picamera2.encoders import H264Encoder



def main_video(video_title, duration, picam2=None):
    # --- Ensure output directory exists ---
    video_dir = "./videos"
    os.makedirs(video_dir, exist_ok=True)

    # --- Define output path ---
    output_path = str(os.path.join(video_dir, f"{video_title}.mp4"))

    if picam2 is None:
    # --- Initialize camera ---
        picam2 = Picamera2()

    print(f" Recording started... Saving to {output_path}")
    picam2.start_recording(H264Encoder(bitrate=10_000_000),FfmpegOutput(output_path))


    # --- Record duration (10 s example, or change as needed) ---
    time.sleep(duration)

    # --- Stop recording ---
    picam2.stop_recording()
    print(f" Recording complete. File saved as: {output_path}")

if __name__ == "__main__":
    video_title = 'original_title'
    duration = 60
    if len(sys.argv) > 2:
        video_title = "_".join(sys.argv[1:]).replace(" ", "_")
        print(f"video title: {video_title}")
        duration = int(sys.argv[-1])
        print(f"duration: {duration}")
        
    main_video(video_title, duration)
