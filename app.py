# USAGE
# python webstreaming.py --ip 0.0.0.0 --port 8000

# import the necessary packages
from imageprocessors.motion_detection import SingleMotionDetector
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
from flask import g
from flask import request
from flask import redirect
from flask import url_for
import threading
import argparse
import datetime
import imutils
import time
import cv2
import sqlite3
from flask import jsonify
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions
import settings

DATABASE = 'database.db'

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing tthe stream)
outputFrame = {}
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__, 
			static_url_path='', 
			static_folder='client/static', 
			template_folder='client/templates')

@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code

for ex in default_exceptions:
    app.register_error_handler(ex, handle_error)


app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['BUNDLE_ERRORS'] = settings.BUNDLE_ERRORS

db = SQLAlchemy(app)
api = Api(app)
api.prefix = '/api'
from endpoints.cams.model import Cam
from endpoints.cams.resource import CamsResource
api.add_resource(CamsResource, '/cams', '/cams/<int:cam_id>')



@app.route("/")
def index():
    cams = Cam.query.all()
    return render_template("index.html", cams = cams)

@app.route('/video_feed/<int:id>/', methods=["GET"])
def video_feed(id):
	return Response(generate(id), mimetype = "multipart/x-mixed-replace; boundary=frame")

def capture_stream(cam):
	frameCount = 32
	# grab global references to the video stream, output frame, and
	# lock variables
	global outputFrame, lock
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
		frame = imutils.resize(frame, width=1280)
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
		with lock:
			outputFrame[cam.id] = frame.copy()
	vs.release()





def generate(id):
	# grab global references to the output frame and lock variables
	global outputFrame, lock

	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if outputFrame[id] is None:
				continue

			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame[id])

			# ensure the frame was successfully encoded
			if not flag:
				continue

		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

def startMonitoringThread(cam):
	global outputFrame
	outputFrame[cam.id] = None
	t = threading.Thread(target=capture_stream, args=(cam,))
	t.daemon = True
	t.start()

# check to see if this is the main thread of execution
def webstreaming():
	# construct the argument parser and parse command line arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, required=True,
		help="ip address of the device")
	ap.add_argument("-o", "--port", type=int, required=True,
		help="ephemeral port number of the server (1024 to 65535)")
	ap.add_argument("-f", "--frame-count", type=int, default=32,
		help="# of frames used to construct the background model")
	args = vars(ap.parse_args())

	# read cams from db
	with app.app_context():
		cams = Cam.query.all()
		for cam in cams:
			# start a thread that will perform motion detection for each cam
			startMonitoringThread(cam)

	# start the flask app
	app.run(host=args["ip"], port=args["port"], debug=True,
		threaded=True, use_reloader=False)

# release the video stream pointer
