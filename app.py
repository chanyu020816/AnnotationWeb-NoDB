import base64
import io
import os
import re
import zipfile
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, send_file, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from pascal_voc_writer import Writer
from PIL import Image as pilImage
from sqlalchemy import inspect

from config import *
from flask_session import Session
from utils.database import *
from utils.website_utils import *
from utils.WMTS_crawler import (
    download_WMTS_images,
    get_surrounding_tile_range,
    lonlat_to_tile,
)

DATABASE = False
TEMP_FOLDER = "Database" if DATABASE else "No-Database"
db = None

app = Flask(__name__)
app.secret_key = "app"
app.config["SESSION_TYPE"] = "filesystem"
if DATABASE:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://admin01:symboldetection@localhost:8001/symboldetection"  # docker only database, app.py local
    )
    db = SQLAlchemy(app)
Session(app)

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

if db:

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


@app.route("/")
def index():
    return render_template(os.path.join(TEMP_FOLDER, "index.html"))


@app.route("/label_page")
def label_page():
    return (
        render_template(os.path.join(TEMP_FOLDER, "label_page.html"))
        if "logged_in" in session
        else redirect("/")
    )


@app.route("/WMTSlabel_page")
def WMTSlabel_page():
    return (
        render_template(os.path.join(TEMP_FOLDER, "WMTSlabel_page.html"))
        if "logged_in" in session
        else redirect("/")
    )


@app.route("/nav_1904")
def nav_1904():
    return render_template(os.path.join(TEMP_FOLDER, "nav_1904.html"))


@app.route("/nav_1921")
def nav_1921():
    return render_template(os.path.join(TEMP_FOLDER, "nav_1921.html"))


@app.route(f"/validate_password", methods=["POST"])
def validate_password():
    data = request.json
    username_input = data["username"]
    password_input = data["password"]

    if not DATABASE:
        session["logged_in"] = True
        session["username"] = username_input
        return jsonify({"success": True}), 200

    user = User.query.filter_by(username=username_input).first()
    if user and user.password == password_input:
        session["logged_in"] = True
        session["username"] = username_input
        return jsonify({"success": True}), 200
    else:
        return (
            jsonify({"success": False, "message": "Incorrect username or password"}),
            401,
        )


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("username", None)
    return redirect("/")


@app.route("/save_image_for_download", methods=["POST"])
def save_image_for_download():
    data = request.json
    image_data = data["image_data"]
    image_name = data["image_name"]
    image_name = re.sub(r"\s+", "_", image_name)
    image_folder_path = os.path.join("Annotations", f"Server_images")

    output_path = os.path.join(image_folder_path, f"{image_name}.jpg")
    image_data = image_data.split(",")[
        1
    ]  # Remove the prefix of Base64 encoding if present
    image_bytes = base64.b64decode(image_data)

    image = pilImage.open(io.BytesIO(image_bytes))
    image = image.convert("RGB")
    image.save(output_path)

    return jsonify({"message": "Image Saved Successfully."})


@app.route("/save_image", methods=["POST"])
def save_image():
    data = request.json
    image_data = data["image_data"]
    image_name = data["image_name"]
    image_name = re.sub(r"\s+", "_", image_name)
    set = data["class_set"]
    username = data["username"]

    image_folder_path = os.path.join(
        "Annotations", f"Yolo_AnnotationsSet{set}", "images"
    )
    output_path = os.path.join(image_folder_path, f"{image_name}.jpg")

    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)

    image = pilImage.open(io.BytesIO(image_bytes))
    image = image.convert("RGB")
    image.save(output_path)

    # save to server
    server_image_folder_path = os.path.join(
        "Annotations", f"Server_AnnotationsSet{set}", "images"
    )
    image.save(os.path.join(server_image_folder_path, f"{image_name}.jpg"))

    with open(os.path.join("Annotations", "log.csv"), "a") as f:
        f.write(f"{username}, {image_name}.jpg, {datetime.now()} \n")
    return jsonify({"message": "Image Saved Successfully."})


@app.route("/save_annotations", methods=["POST"])
def save_annotations():
    data = request.json
    image_name = data["image_name"]
    image_name = re.sub(r"\s+", "_", image_name)
    format_type = data["format_type"]
    yolo_labels = data["yolo_labels"]
    image_size = data["img_size"]
    set = data["class_set"]
    if format_type == "yolo":
        label_folder_path = os.path.join(
            "Annotations", f"Yolo_AnnotationsSet{set}", "labels"
        )
        output_path = os.path.join(label_folder_path, f"{image_name}.txt")
        with open(output_path, "w") as file:
            for label in yolo_labels:
                id, x, y, w, h, _ = get_values(label)
                file.write(f"{id} {x} {y} {w} {h} " + "\n")

    elif format_type == "pascal":
        voc_folder_path = os.path.join("Annotations", f"PASCAL_AnnotationsSet{set}")
        """ 
        # create pascal voc writer (image_path, width, height)
        writer = Writer('path/to/img.jpg', 800, 598)

        # add objects (class, xmin, ymin, xmax, ymax)
        writer.addObject('truck', 1, 719, 630, 468)
        writer.addObject('person', 40, 90, 100, 150)

        # write to file
        writer.save('path/to/img.xml')
        """

        writer = Writer(
            os.path.join(voc_folder_path, f"{image_name}.jpg"), image_size, image_size
        )
        for label in yolo_labels:
            id, x, y, w, h, _ = get_values(label)

            x *= image_size
            y *= image_size
            w *= image_size
            h *= image_size
            x1 = x - w / 2
            y1 = y - h / 2
            x2 = x + w / 2
            y2 = y + h / 2
            writer.addObject(CLASSES[set - 1][id], x1, y1, x2, y2)
        writer.save(os.path.join(voc_folder_path, f"{image_name}.xml"))

    label_folder_path = os.path.join(
        "Annotations", f"Server_AnnotationsSet{set}", "labels"
    )
    output_path = os.path.join(label_folder_path, f"{image_name}.txt")
    with open(output_path, "w") as file:

        for label in yolo_labels:
            id, x, y, w, h, _ = get_values(label)
            file.write(f"{id} {x} {y} {w} {h} " + "\n")

        writer = Writer(
            os.path.join(
                "Annotations", f"Server_AnnotationsSet{set}", f"{image_name}.jpg"
            ),
            image_size,
            image_size,
        )
        for label in yolo_labels:
            id, x, y, w, h, _ = get_values(label)
            x *= image_size
            y *= image_size
            w *= image_size
            h *= image_size
            x1 = x - w / 2
            y1 = y - h / 2
            x2 = x + w / 2
            y2 = y + h / 2
            writer.addObject(CLASSES[set - 1][id], x1, y1, x2, y2)
        writer.save(os.path.join(label_folder_path, f"{image_name}.xml"))

    return jsonify({"message": "Success"})


@app.route("/add_img_db", methods=["POST"])
def add_img_db():

    if not DATABASE:
        return jsonify({"success": True}), 200

    data = request.json
    username = data["username"]
    parentimg = data["parent_image"]
    child_imgs = data["child_images"]
    img_name = parentimg["name"]
    width = parentimg["width"]
    height = parentimg["height"]
    split_size = parentimg["split_size"]
    img_name = re.sub(r"\s+", "_", img_name)
    existing_parentimg = ParentImage.query.filter_by(
        imagename=img_name, width=width, height=height, split_size=split_size
    ).first()
    if existing_parentimg:
        return jsonify({"success": True}), 200
    else:
        user = User.query.filter_by(username=username).first()
        user_id = user.id
        # add parent image to db
        parentimg = ParentImage(img_name, user_id, width, height, split_size)
        db.session.add(parentimg)
        db.session.commit()
        parentimg_id = parentimg.id

        # add child image to db
        for child_img in child_imgs:
            """
            {'name': 'Screenshot 2024-04-10 at 4.09.19\u202fPM_h0_w0', 'location': [0, 0], 'paddings': [204, 236, 480, 480]}
            """
            h, w = child_img["location"]
            x1, y1, x2, y2 = child_img["paddings"]
            img = Image(
                imagename=re.sub(r"\s+", "_", child_img["name"]),
                parentimage_id=parentimg_id,
                loaction_h=h,
                location_w=w,
                padding_xmin=x1,
                padding_ymin=y1,
                padding_xmax=x2,
                padding_ymax=y2,
            )
            db.session.add(img)
        db.session.commit()
        return jsonify({"success": True}), 200


@app.route("/add_labels_db", methods=["POST"])
def add_labels():

    if not DATABASE:
        return jsonify({"success": True}), 200

    data = request.json
    username = data["username"]
    imagename = data["image_name"]
    imagename = re.sub(r"\s+", "_", imagename)
    yolo_labels = data["yolo_labels"]
    set = data["class_set"]
    label_file_path = os.path.join(
        "Annotations", f"Server_AnnotationsSet{set}", "labels", f"{imagename}.txt"
    )
    user = User.query.filter_by(username=username).first()
    user_id = user.id
    image = Image.query.filter_by(imagename=imagename).first()
    image_id = image.id

    label_history = LabelHistory(image_id, user_id, datetime.now(), label_file_path)
    db.session.add(label_history)
    db.session.commit()
    label_history_id = label_history.id

    # add labels
    for label in yolo_labels:
        id, x, y, w, h, _ = get_values(label)
        label = Labels(label_history_id, set, id, x, y, w, h)
        db.session.add(label)

    image.is_labeled = True
    db.session.commit()

    return jsonify({"success": True}), 200


@app.route("/download_annotations", methods=["GET"])
def download_annotations():
    class_set = request.args.get("class_set")
    completed_file_names = request.args.get("filenames").split(",")
    format_type = request.args.get("format_type")

    zip_filename = "annotations.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for file in completed_file_names:
            filename = re.sub(r"\s+", "_", file)
            replace_chars = {"[": "", "]": "", '"': ""}
            filename = "".join(replace_chars.get(c, c) for c in filename)

            if format_type == "yolo":
                image_file_path = os.path.join(
                    "./Annotations",
                    f"Server_AnnotationsSet{class_set}",
                    "images",
                    f"{filename}.jpg",
                )
                label_file_path = os.path.join(
                    "./Annotations",
                    f"Server_AnnotationsSet{class_set}",
                    "labels",
                    f"{filename}.txt",
                )

                zipf.write(
                    image_file_path,
                    arcname=os.path.join("images", os.path.basename(image_file_path)),
                )
                zipf.write(
                    label_file_path,
                    arcname=os.path.join("labels", os.path.basename(label_file_path)),
                )

    return send_file(zip_filename, as_attachment=True)


@app.route("/download_WMTSannotations", methods=["GET"])
def download_WMTSannotations():
    class_set = request.args.get("class_set")
    completed_file_names = request.args.get("filenames").split(",")
    format_type = request.args.get("format_type")

    WMTS_folder = os.path.join(
        "./Annotations", f"Server_AnnotationsSet{class_set}_WMTS"
    )
    WMTS_image_folder = os.path.join(
        "./Annotations", f"Server_AnnotationsSet{class_set}_WMTS", "images"
    )
    WMTS_label_folder = os.path.join(
        "./Annotations", f"Server_AnnotationsSet{class_set}_WMTS", "labels"
    )
    zip_filename = "annotations.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for file in completed_file_names:
            filename = re.sub(r"\s+", "_", file)
            replace_chars = {"[": "", "]": "", '"': ""}
            filename = "".join(replace_chars.get(c, c) for c in filename)

            image_file_path = os.path.join(
                "./Annotations",
                f"Server_AnnotationsSet{class_set}",
                "images",
                f"{filename}.jpg",
            )
            label_file_path = os.path.join(
                "./Annotations",
                f"Server_AnnotationsSet{class_set}",
                "labels",
                f"{filename}.txt",
            )

            remove_paddings_result = WMTS_remove_paddings(
                image_file_path, label_file_path
            )

            image_file_path_rm_padding = os.path.join(
                WMTS_image_folder,
                f"{filename}.jpg",
            )
            img = remove_paddings_result["img"]
            img.save(image_file_path_rm_padding)

            label_file_path_rm_padding = os.path.join(
                WMTS_label_folder,
                f"{filename}.txt",
            )

            labels = remove_paddings_result["label"]
            with open(label_file_path_rm_padding, "w") as f:
                for label in labels:
                    for value in label:
                        f.write(f"{value} ")
                    f.write("\n")

            zipf.write(
                image_file_path_rm_padding,
                arcname=os.path.join(
                    "images", os.path.basename(image_file_path_rm_padding)
                ),
            )
            zipf.write(
                label_file_path_rm_padding,
                arcname=os.path.join(
                    "labels", os.path.basename(label_file_path_rm_padding)
                ),
            )

    return send_file(zip_filename, as_attachment=True)


@app.route("/download_image", methods=["GET"])
def download_image():
    filename = request.args.get("filenames")
    image_name = re.sub(r"\s+", "_", filename)
    image_name = image_name.replace('"', "")
    image_file_path = os.path.join("Annotations", f"Server_images", f"{image_name}.jpg")
    return send_file(image_file_path, as_attachment=True)


@app.route("/download_wmts_image", methods=["POST"])
def download_wmts_image():
    save_folder = "./Annotations/Server_images"

    data = request.json
    x_tile = data.get("x_tile")
    y_tile = data.get("y_tile")
    year = int(data.get("year"))
    zoom = int(data.get("zoom"))
    # x_tile, y_tile = lonlat_to_tile(float(lon), float(lat), 16)
    x_tile_start, x_tile_end, y_tile_start, y_tile_end = get_surrounding_tile_range(
        x_tile, y_tile
    )
    download_WMTS_images(
        save_folder=save_folder,
        x_tile_start=x_tile_start,
        x_tile_end=x_tile_end + 1,
        y_tile_start=y_tile_start,
        y_tile_end=y_tile_end + 1,
        zoom_level=zoom,
        year=year,
    )

    file_list = []
    for x in range(x_tile_start, x_tile_end + 1):
        for y in range(y_tile_start, y_tile_end + 1):
            file_name = f"{year}-{zoom}-{x}-{y}.jpg"
            file_path = f"{save_folder}/{file_name}"
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    file_content = base64.b64encode(file.read()).decode("utf-8")
                    file_list.append(
                        {
                            "name": file_name,
                            "content": file_content,
                            "type": "image/jpg",
                        }
                    )
            else:
                print(f"Failed: {file_path}")
    return jsonify({"message": "Success", "files": file_list})


@app.route("/upload_yolo_labels", methods=["POST"])
def upload_yolo_labels():
    if "file" not in request.files:
        return "no labels", 400

    files = request.files.getlist("file")
    if len(files) == 0:
        return "no labels", 400

    labels = []
    for file in files:
        if file and file.filename.endswith(".txt"):
            filename = file.filename
            existing_image = (
                Image.query.filter_by(filename=filename).first() if DATABASE else True
            )
            if existing_image:
                label_data = parse_label_file(file)
                if label_data:
                    labels.append(label_data)
            else:
                return "not found in database", 400
    return jsonify(labels)


def check_folder_exists():

    create_img_label_folder("./Annotations")
    create_folder(os.path.join("./Annotations", "Server_images"))
    for class_set in range(1, 3):
        create_img_label_folder(
            os.path.join("./Annotations", f"Server_AnnotationsSet{class_set}_WMTS")
        )
        create_img_label_folder(
            os.path.join("./Annotations", f"Server_AnnotationsSet{class_set}")
        )
        create_img_label_folder(
            os.path.join("./Annotations", f"Server_AnnotationsSet{class_set}")
        )

        create_img_label_folder(
            os.path.join("./Annotations", f"Yolo_AnnotationsSet{class_set}")
        )


if __name__ == "__main__":
    check_folder_exists()

    app.run(host="0.0.0.0", port=8000, debug=True)
