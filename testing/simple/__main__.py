import os
from multiprocessing import Process
from runner import runner
if __name__ == '__main__':
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;0" # Ensure OpenCV uses UDP streams
    p = Process(target=runner)
    p.start()
    p.join()