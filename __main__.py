import os
import sys
from multiprocessing import Process
from app import webstreaming
if __name__ == '__main__':
    try:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;0" # Ensure OpenCV uses UDP streams
        p = Process(target=webstreaming)
        p.start()
        p.join()
    except KeyboardInterrupt:
        sys.exit()