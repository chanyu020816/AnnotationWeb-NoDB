from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(80), nullable=False)

    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role

    def __repr__(self):
        return "<User %r>" % self.username


class ParentImage(db.Model):
    __tablename__ = "parentimage"

    id = db.Column(db.Integer, primary_key=True)
    imagename = db.Column(db.String(80), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    split_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, imagename, user_id, width, height, split_size):
        self.imagename = imagename
        self.user_id = user_id
        self.width = width
        self.height = height
        self.split_size = split_size

    def __repr__(self):
        return f"<ParentImage {self.id}>"


class Image(db.Model):
    __tablename__ = "image"

    id = db.Column(db.Integer, primary_key=True)
    imagename = db.Column(db.String(80), unique=True, nullable=False)
    parentimage_id = db.Column(
        db.Integer, db.ForeignKey("parentimage.id"), nullable=False
    )
    parentimage = db.relationship(
        "ParentImage", backref=db.backref("images", lazy=True)
    )
    location_h = db.Column(db.Integer, nullable=False)
    location_w = db.Column(db.Integer, nullable=False)
    padding_xmin = db.Column(db.Integer, nullable=False)
    padding_ymin = db.Column(db.Integer, nullable=False)
    padding_xmax = db.Column(db.Integer, nullable=False)
    padding_ymax = db.Column(db.Integer, nullable=False)
    is_labeled = db.Column(db.Boolean, default=False)

    def __init__(
        self,
        imagename,
        parentimage_id,
        loaction_h,
        location_w,
        padding_xmin,
        padding_ymin,
        padding_xmax,
        padding_ymax,
    ):
        self.imagename = imagename
        self.parentimage_id = parentimage_id
        self.location_h = loaction_h
        self.location_w = location_w
        self.padding_xmin = padding_xmin
        self.padding_ymin = padding_ymin
        self.padding_xmax = padding_xmax
        self.padding_ymax = padding_ymax

    def __repr__(self):
        return f"<Image {self.id}>"


class LabelHistory(db.Model):
    __tablename__ = "labelhistory"

    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey("image.id"), nullable=False)
    image = db.relationship("Image", backref=db.backref("label_history", lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label_date = db.Column(db.DateTime, default=datetime.now)
    label_file_path = db.Column(db.String(200), nullable=False)

    def __init__(self, image_id, user_id, label_date, label_file_path):
        self.image_id = image_id
        self.user_id = user_id
        self.label_date = label_date
        self.label_file_path = label_file_path

    def __repr__(self):
        return f"<LabelHistory {self.id}>"


class Labels(db.Model):
    __tablename__ = "labels"

    id = db.Column(db.Integer, primary_key=True)
    label_history_id = db.Column(
        db.Integer, db.ForeignKey("labelhistory.id"), nullable=False
    )
    label_history = db.relationship(
        "LabelHistory", backref=db.backref("labels", lazy=True)
    )
    class_set = db.Column(db.Integer, nullable=False)
    class_id = db.Column(db.Integer, nullable=False)
    x_center = db.Column(db.Float, nullable=False)
    y_center = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)

    def __init__(
        self, label_history_id, class_set, id, x_center, y_center, width, height
    ):
        self.label_history_id = label_history_id
        self.class_set = class_set
        self.class_id = id
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height

    def __repr__(self):
        return f"<Labels {self.id}>"
