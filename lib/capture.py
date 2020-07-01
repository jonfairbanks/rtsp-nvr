import threading
import cv2
import imutils
import datetime
import time
import np
from lib.imageprocessors.motion_detection import SingleMotionDetector

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
		self.timestamp = cam.timestamp
		self.fps = 1/60
	def run(self):
		vs = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
		time.sleep(1)
		while self.running:
			# loop over frames from the video stream
			if self.connected: # read the frame from video stream
				success, frame = vs.read()
				#frame = imutils.resize(frame, width=1280)
				

				

				# acquire the lock, set the output frame, and release the
				if success:# lock
					with lock:
						# grab the current timestamp and draw it on the frame
						if self.timestamp:
							timestamp = datetime.datetime.now()
							cv2.putText(frame, timestamp.strftime(
								"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
								cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
						self.outputFrame = frame.copy()
				else:
					vs.release()
					self.connected = False
					with lock:
						red = (255, 0, 0)
						frame = create_frame(1280,720,"device disconnected",rgb_color=red)
						self.outputFrame = frame
				
			else:
				print('trying to connect to cam', self.name)
				vs = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
				time.sleep(1)
				self.connected = True	
			time.sleep(self.fps)
					
		vs.release()

		with lock:
			blue = (0, 0, 255)
			frame = create_frame(1280,720,"device stopped",rgb_color=blue)
			self.outputFrame = frame

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

def deleteCaptureDevice(cam):
	capDevice = Devices[cam.id]
	capDevice.stop()
	Devices.pop(cam.id, None)

def generateFrames(id):
	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if id in Devices:
				if Devices[id].outputFrame is None:
					continue

				# encode the frame in JPEG format
				(flag, encodedImage) = cv2.imencode(".jpg", Devices[id].outputFrame)

				# ensure the frame was successfully encoded
				if not flag:
					continue
			else:
				black = (0, 0, 0)
				frame = create_frame(1280,720,"no device", rgb_color=black)
				(flag, encodedImage) = cv2.imencode(".jpg", frame)
		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')
		time.sleep(Devices[id].fps)

def create_frame(width, height, text, rgb_color=(50, 50, 50),):
    # Create black blank image
    frame = np.zeros((height, width, 3), np.uint8)
    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    frame[:] = color
	# Add text to frame
    cv2.putText(frame, text, (10, frame.shape[0] - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    return frame