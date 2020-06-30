# import the necessary packages
import argparse
from flask import Response
from flask import Flask
from flask import render_template
from flask import jsonify
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions
import settings


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

from lib import capture

# Define Routes
@app.route("/")
def index():
    cams = Cam.query.all()
    return render_template("index.html", cams = cams)

@app.route("/admin")
def admin():
    cams = Cam.query.all()
    return render_template("admin.html", cams = cams)

@app.route('/video_feed/<int:id>/', methods=["GET"])
def video_feed(id):
	return Response(capture.generateFrames(id), mimetype = "multipart/x-mixed-replace; boundary=frame")

# Main function
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
			capture.startCaptureDevice(cam)

	# start the flask app
	app.run(host=args["ip"], port=args["port"], debug=True,
		threaded=True, use_reloader=False)
