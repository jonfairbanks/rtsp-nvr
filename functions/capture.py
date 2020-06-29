import threading
import cv2
import imutils
import datetime
import time
import globfile
from imageprocessors.motion_detection import SingleMotionDetector

def startMonitoringThread(cam):
	globfile.outputFrame[cam.id] = None
	t = threading.Thread(target=capture_stream, args=(cam,))
	t.daemon = True
	t.start()

def capture_stream(cam):

	frameCount = 32

	# initialize the video stream and allow the camera sensor to
	# warmup
	vs = cv2.VideoCapture(cam.url, cv2.CAP_FFMPEG)
	time.sleep(2.0)
	
	# initialize the motion detector and the total number of frames
	# read thus far
	md = SingleMotionDetector(accumWeight=0.1)
	total = 0

	# loop over frames from the video stream
	while True:
		# read the next frame from the video stream, resize it,
		# convert the frame to grayscale, and blur it
		f, frame = vs.read()
		frame = imutils.resize(frame, width=400)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (7, 7), 0)

		# grab the current timestamp and draw it on the frame
		timestamp = datetime.datetime.now()
		cv2.putText(frame, timestamp.strftime(
			"%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
			cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

		# if the total number of frames has reached a sufficient
		# number to construct a reasonable background model, then
		# continue to process the frame
		if total > frameCount:
			# detect motion in the image
			motion = md.detect(gray)

			# cehck to see if motion was found in the frame
			if motion is not None:
				# unpack the tuple and draw the box surrounding the
				# "motion area" on the output frame
				(thresh, (minX, minY, maxX, maxY)) = motion
				cv2.rectangle(frame, (minX, minY), (maxX, maxY),
					(0, 0, 255), 2)
		
		# update the background model and increment the total number
		# of frames read thus far
		md.update(gray)
		total += 1

		# acquire the lock, set the output frame, and release the
		# lock
		with globfile.lock:
			globfile.outputFrame[cam.id] = frame.copy()
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