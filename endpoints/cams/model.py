from app import db


class Cam(db.Model):
    __tablename__ = 'cam'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    url = db.Column(db.String(200))
    running = db.Column(db.Boolean, unique=False, default=True)
    timestamp = db.Column(db.Boolean, unique=False, default=True)

    def __repr__(self):
        return 'Id: {}, name: {}, url: {}'.format(self.id, self.name, self.url)