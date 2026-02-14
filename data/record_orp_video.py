import threading
import os
import sys
import time
import record_orp as orp_obj
import record_video as vid_obj
import argparse
from picamera2 import Picamera2
from stepper import stepper_worker


def main(duration, video_title, is_video, is_orp):
    print("initializing threads")
    init_threads(duration, video_title, is_video, is_orp)


def init_threads(duration, video_title, is_video, is_orp):
        '''creates threads that will record data for orp and record data for the video'''
        threads = []
        sw = threading.Thread(target=stepper_worker)
        threads.append(sw)
        if is_orp:
            args_orp = [duration, video_title]
            t1 = threading.Thread(target=orp_obj.main_orp, args=args_orp)
            threads.append(t1)

        if is_video:
            picam2 = Picamera2()
            args_vid = [video_title, duration, picam2]
            t2 = threading.Thread(target=vid_obj.main_video, args=args_vid)
            threads.append(t2)
        
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        print("data collection completed")


parser = argparse.ArgumentParser()
parser.add_argument("video_title", help="concentration and reaction type, example : 12ST10H20")
parser.add_argument("duration", help="duration of the reaction")
parser.add_argument("-b", "-ov", "-a", "--all", action="store_true", help="please indicate if you want to use ORP and video -b")
parser.add_argument("-o", action="store_true", help="please indicate if you want to use ORP -o")
parser.add_argument("-v", action="store_true", help="please indicate if you want to use video -v")

args = parser.parse_args()

if __name__ == '__main__':
    print(args)
    duration = int(args.duration)
    video_title = args.video_title

    orp = False
    vid = False
    if args.o:
         orp = True
    if args.v:
         vid = True
    if args.all:
         orp = True
         vid = True

    main(duration=duration, video_title=video_title, is_video=vid, is_orp=orp)
    
   


        
    

    
