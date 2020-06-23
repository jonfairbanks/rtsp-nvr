import cv2
import numpy as np
def capture():
    i = 0
    camera = cv2.VideoCapture("rtsp://192.168.0.30:5554", cv2.CAP_FFMPEG)
    video  = cv2.VideoWriter('stream.avi', -1, 15, (1920, 1080));
    while True:
        f,img = camera.read()
        cv2.imshow("RTSP NVR",img) # Open Stream Window
        # video.write(img) # Save Stream to File -- WIP
        cv2.imwrite('{0:05d}.jpg'.format(i),img) # Save stream as images
        i += 1
        if cv2.waitKey(16) == ord("q"):
            break
    video.release()