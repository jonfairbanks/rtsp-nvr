import threading
import cv2
import imutils
import datetime
import time
import np
from imageprocessors.motion_detection import SingleMotionDetector

from threading import Thread
from endpoints.cams.model import Cam
lock = threading.Lock()
Devices = {}

class CaptureDevice(Thread):
	daemon = True
	def __init__(self, cam):
		super().__init__()
		self.running = cam.running
		self.name = cam.name
		self.url = cam.url
		self.outputFrame = None
		self.connected = True
	def run(self):
		while self.running:
			vs = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
			time.sleep(1)
			# loop over frames from the video stream
			while True:
				if self.connected: # read the frame from video stream
					success, frame = vs.read()
					#frame = imutils.resize(frame, width=1280)
					

					# grab the current timestamp and draw it on the frame
					#timestamp = datetime.datetime.now()
					#cv2.putText(frame, timestamp.strftime(
						#"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
						#cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

					# acquire the lock, set the output frame, and release the
					if success:# lock
						with lock:
							self.outputFrame = frame.copy()
					else:
						vs.release()
						self.connected = False
						with lock:
							red = (255, 0, 0)
							blank_image = create_blank(1280,720,rgb_color=red)
							self.outputFrame = blank_image
				else:
					print('trying to connect to cam', self.name)
					vs = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
					time.sleep(1)
					self.connected = True		
			vs.release()
		with lock:
			blue = (0, 0, 255)
			blank_image = create_blank(1280,720,rgb_color=blue)
			self.outputFrame = blank_image

	def stop(self):
		self.running = False


def startCaptureDevice(cam):
	# Create new capture device from cam info
	capDevice = CaptureDevice(cam)
	# call start method, to initialize thread/run function of the CaptureDevice class
	capDevice.start()
	# add Capture device by id to global dictionary of all active devices
	Devices[cam.id] = capDevice

def setCaptureDevice(cam):
	capDevice = Devices[cam.id]
	capDevice.stop()
	startCaptureDevice(cam)

def generateFrames(id):
	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if Devices[id].outputFrame is None:
				continue

			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", Devices[id].outputFrame)

			# ensure the frame was successfully encoded
			if not flag:
				continue

		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

def create_blank(width, height, rgb_color=(50, 50, 50)):
    # Create black blank image
    image = np.zeros((height, width, 3), np.uint8)

    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    image[:] = color

    return image