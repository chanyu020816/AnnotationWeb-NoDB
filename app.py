import base64
import csv
import io
import json
import os
import re
import shutil
import zipfile
from datetime import datetime

import numpy as np
import yaml
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from pascal_voc_writer import Writer
from PIL import Image as pilImage

# from utils.image_padding import ImagePadding
from utils.WMTS_crawler import (
    download_WMTS_images,
    get_surrounding_tile_range,
    lonlat_to_tile,
)
from utils.WMTS_utils import labels_to_lonlat, modify_labels, remove_padding

DISPLAY_SIZE = 720

app = Flask(__name__)

class1 = ["田地", "草地", "荒地", "墓地", "樹林", "竹林", "旱地", "茶畑"]
class2 = [
    "果園",
    "茶畑",
    "桑畑",
    "沼田",
    "水田",
    "乾田",
    "荒地",
    "樹林椶櫚科",
    "竹林",
    "樹林鍼葉",
    "樹林濶葉",
    "草地",
]
classes = [class1, class2]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/label_page")
def label_page():
    return render_template("label_page.html")


@app.route("/WMTSlabel_page")
def WMTSlabel_page():
    return render_template("WMTSlabel_page.html")


@app.route("/nav_1904")
def nav_1904():
    return render_template("nav_1904.html")


@app.route("/nav_1921")
def nav_1921():
    return render_template("nav_1921.html")


@app.route("/save_image_for_download", methods=["POST"])
def save_image_for_download():
    data = request.json
    image_data = data["image_data"]
    image_name = data["image_name"]
    image_name = re.sub(r"\s+", "_", image_name)
    image_folder_path = os.path.join("Annotations", f"Server_images")
    if not os.path.exists(image_folder_path):
        os.mkdir(image_folder_path)

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
    format_type = data["format_type"]
    set = data["class_set"]
    username = data["username"]
    if format_type == "yolo":
        image_folder_path = os.path.join(
            "Annotations", f"Yolo_AnnotationsSet{set}", "images"
        )
        if not os.path.exists(os.path.join("Annotations", f"Yolo_AnnotationsSet{set}")):
            os.mkdir(os.path.join("Annotations", f"Yolo_AnnotationsSet{set}"))
        if not os.path.exists(image_folder_path):
            os.mkdir(image_folder_path)
    elif format_type == "pascal":
        image_folder_path = os.path.join("Annotations", f"PASCAL_AnnotationsSet{set}")
        if not os.path.exists(image_folder_path):
            os.mkdir(image_folder_path)

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
    if not os.path.exists(os.path.join("Annotations", f"Server_AnnotationsSet{set}")):
        os.mkdir(os.path.join("Annotations", f"Server_AnnotationsSet{set}"))
    if not os.path.exists(server_image_folder_path):
        os.mkdir(server_image_folder_path)
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
    print(image_name)
    if format_type == "yolo":
        label_folder_path = os.path.join(
            "Annotations", f"Yolo_AnnotationsSet{set}", "labels"
        )
        if not os.path.exists(label_folder_path):
            os.mkdir(label_folder_path)
        output_path = os.path.join(label_folder_path, f"{image_name}.txt")
        print(output_path)
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
            writer.addObject(classes[set - 1][id], x1, y1, x2, y2)
        writer.save(os.path.join(voc_folder_path, f"{image_name}.xml"))

    label_folder_path = os.path.join(
        "Annotations", f"Server_AnnotationsSet{set}", "labels"
    )
    if not os.path.exists(label_folder_path):
        os.mkdir(label_folder_path)
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
            writer.addObject(classes[set - 1][id], x1, y1, x2, y2)
        writer.save(os.path.join(label_folder_path, f"{image_name}.xml"))

    return jsonify({"message": "Success"})


def get_values(label):
    return [label["id"], label["x"], label["y"], label["w"], label["h"], "work"]


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
            else:
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
                    f"{filename}.xml",
                )

                zipf.write(
                    image_file_path,
                    arcname=os.path.join(
                        "annotations", os.path.basename(image_file_path)
                    ),
                )
                zipf.write(
                    label_file_path,
                    arcname=os.path.join(
                        "annotations", os.path.basename(label_file_path)
                    ),
                )

    return send_file(zip_filename, as_attachment=True)


def create_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return


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
    create_folder(WMTS_folder)
    create_folder(WMTS_image_folder)
    create_folder(WMTS_label_folder)

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
                    print(labels)
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


def WMTS_remove_paddings(image_path, label_path):
    img = pilImage.open(image_path)
    img_arr = np.array(img)
    img = remove_padding(img_arr, 256)

    labels = []
    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            label = [int(parts[0])] + [float(x) for x in parts[1:]]
            labels.append(label)
    labels = modify_labels(labels, 480, 256)

    return {"img": pilImage.fromarray(img), "label": labels}


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
    print(x_tile_start, x_tile_end, y_tile_start, y_tile_end, zoom, year)
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
            # existing_image = Image.query.filter_by(filename=filename).first()
            existing_image = True
            if existing_image:
                label_data = parse_label_file(file)
                if label_data:
                    labels.append(label_data)
            else:
                return "not found in database", 400
    return jsonify(labels)


def parse_label_file(file):
    labels = []
    annos = []
    anno_id = 0
    for line in file:
        parts = line.strip().split()
        if len(parts) == 5:
            class_id, x_center, y_center, width, height = map(float, parts)
            labels.append(
                {
                    "id": class_id,
                    "x": x_center,
                    "y": y_center,
                    "w": width,
                    "h": height,
                    "anno_id": anno_id,
                }
            )
            aug_w = width * DISPLAY_SIZE
            aug_h = height * DISPLAY_SIZE
            annos.append(
                {
                    "id": class_id,
                    "x": x_center * DISPLAY_SIZE - aug_w / 2,
                    "y": y_center * DISPLAY_SIZE - aug_h / 2,
                    "w": aug_w,
                    "h": aug_h,
                    "anno_id": anno_id,
                }
            )
            anno_id += 1

    filename = file.filename[:-4]
    return (
        {"filename": filename, "labels": labels, "annos": annos, "anno_id": anno_id}
        if labels
        else None
    )


if __name__ == "__main__":
    if not os.path.exists("./Annotations"):
        os.mkdir("./Annotations")

    app.run(host="0.0.0.0", port=8000, debug=True)
