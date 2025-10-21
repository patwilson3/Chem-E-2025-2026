import threading
import os
import sys
import time
import record_orp as orp
import record_video as vid
import argparse


def main(duration, video_title, is_video, is_orp):
    if is_video and is_orp:
        print("initializing threads")
        init_threads(duration, video_title)
    elif is_video:
        vid.main_video(video_title, duration)
    else:
        orp.main_orp(duration)


def init_threads(duration, video_title):
        '''creates threads that will record data for orp and record data for the video'''
        args_vid = [video_title, duration]
        args_orp = [duration]
        t1 = threading.Thread(target=orp.main_orp, arg=args_orp)
        t2 = threading.Thread(target=vid.main_video, args=args_vid)
        threads = [t1, t2]
        t1.start()
        t2.start()

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
    
   


        
    

    