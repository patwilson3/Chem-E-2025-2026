import os
import sys
import time
from datetime import datetime
from picamera2 import Picamera2

def main():
    # --- Ensure output directory exists ---
    video_dir = "./videos"
    os.makedirs(video_dir, exist_ok=True)

    # --- Parse optional command line argument ---
    if len(sys.argv) > 2:
        video_title = "_".join(sys.argv[1:]).replace(" ", "_")
        print(f"video title: {video_title}")
        duration = int(sys.argv[-1])
        print(f"duration: {duration}")
    else:
        video_title = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        duration = 100

    # --- Define output path ---
    output_path = os.path.join(video_dir, f"{video_title}.mp4")

    # --- Initialize camera ---
    picam2 = Picamera2()
    #video_config = picam2.create_video_configuration(main={"size": (640, 480)})
    #picam2.configure(video_config)

    print(f" Recording started... Saving to {output_path}")
    picam2.start_recording(output_path)

    # --- Record duration (10 s example, or change as needed) ---
    time.sleep(duration)

    # --- Stop recording ---
    picam2.stop_recording()
    print(f" Recording complete. File saved as: {output_path}")

if __name__ == "__main__":
    main()