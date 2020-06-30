from flask_restful import Resource, reqparse, request
from flask_restful import fields, marshal_with, marshal
from .model import Cam
from app import db
from functions import capture

cam_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'url': fields.String,
    'running': fields.Boolean
}

cam_list_fields = {
    'count': fields.Integer,
    'cams': fields.List(fields.Nested(cam_fields)),
}

cam_post_parser = reqparse.RequestParser()
cam_post_parser.add_argument('name', type=str, required=True, location=['json'],
                              help='name parameter is required')
cam_post_parser.add_argument('url', type=str, required=True, location=['json'],
                              help='url parameter is required')


class CamsResource(Resource):
    def get(self, cam_id=None):
        if cam_id:
            cam = Cam.query.filter_by(id=cam_id).first()
            return marshal(cam, cam_fields)
        else:
            args = request.args.to_dict()
            limit = args.get('limit', 0)
            offset = args.get('offset', 0)

            args.pop('limit', None)
            args.pop('offset', None)

            cam = Cam.query.filter_by(**args).order_by(Cam.id)
            if limit:
                cam = cam.limit(limit)

            if offset:
                cam = cam.offset(offset)

            cam = cam.all()

            return marshal({
                'count': len(cam),
                'cams': [marshal(t, cam_fields) for t in cam]
            }, cam_list_fields)

    @marshal_with(cam_fields)
    def post(self):
        args = cam_post_parser.parse_args()

        cam = Cam(**args)
        db.session.add(cam)
        db.session.commit()
        #START MONITORING
        capture.startCaptureDevice(cam)
        return cam

    @marshal_with(cam_fields)
    def put(self, cam_id=None):
        cam = Cam.query.get(cam_id)

        if 'name' in request.json:
            cam.name = request.json['name']

        if 'url' in request.json:
            cam.url = request.json['url']

        if 'running' in request.json:
            cam.running = request.json['running']

        db.session.commit()
        capture.setCaptureDevice(cam)
        return cam

    @marshal_with(cam_fields)
    def delete(self, cam_id=None):
        cam = Cam.query.get(cam_id)

        db.session.delete(cam)
        db.session.commit()
        capture.deleteCaptureDevice(cam)
        return cam