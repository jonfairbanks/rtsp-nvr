import threading
import cv2
import imutils
import datetime
import time
import globfile
import np
from imageprocessors.motion_detection import SingleMotionDetector


def startMonitoringThread(cam):
	cv2.useOptimized()
	globfile.outputFrame[cam.id] = None
	t = threading.Thread(target=capture_stream, args=(cam,))
	t.daemon = True
	t.start()

def capture_stream(cam):

	# initialize the video stream and allow the camera sensor to
	# warmup
	vs = cv2.VideoCapture(cam.url, cv2.CAP_FFMPEG)
	time.sleep(1)
	connected = True
	# loop over frames from the video stream
	while True:
		if connected: # read the frame from video stream
			success, frame = vs.read()
			#frame = imutils.resize(frame, width=1280)
			

			# grab the current timestamp and draw it on the frame
			#timestamp = datetime.datetime.now()
			#cv2.putText(frame, timestamp.strftime(
				#"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
				#cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

			# acquire the lock, set the output frame, and release the
			if success:# lock
				with globfile.lock:
					globfile.outputFrame[cam.id] = frame.copy()
			else:
				vs.release()
				connected = False
				with globfile.lock:
					red = (255, 0, 0)
					blank_image = create_blank(1280,720,rgb_color=red)
					globfile.outputFrame[cam.id] = blank_image
		else:
			print('trying to reconnect to cam')
			vs = cv2.VideoCapture(cam.url, cv2.CAP_FFMPEG)
			time.sleep(1)
			connected = True		
	vs.release()

def generate(id):

	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with globfile.lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if globfile.outputFrame[id] is None:
				continue

			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", globfile.outputFrame[id])

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