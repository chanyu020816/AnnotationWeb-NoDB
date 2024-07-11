from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import re
import zipfile
from PIL import Image as pilImage
import io
import base64
import os
import json
import yaml
import csv
from pascal_voc_writer import Writer
import shutil
from image_padding import ImagePadding
from datetime import datetime


app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://admin01:symboldetection@db/symboldetection' # docker app.py with database
# app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://admin01:symboldetection@localhost:3306/symboldetection' # docker only database, app.py local
# db = SQLAlchemy(app)

class1 = ["田地", "草地", "荒地", "墓地", "樹林", "竹林", "旱地", "茶畑"]
class2 = ["果園", "茶畑", "桑畑", "沼田", "水田", "乾田", "荒地", "樹林椶櫚科", "竹林", "樹林鍼葉", "樹林濶葉", "草地"]
classes = [class1, class2]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_image_for_download', methods=['POST'])
def save_image_for_download():
    data = request.json
    image_data = data['image_data']
    image_name = data["image_name"]
    image_name = re.sub(r'\s+', '_', image_name)
    image_folder_path = os.path.join("Annotations", f"Server_images")
    if not os.path.exists(image_folder_path):
        os.mkdir(image_folder_path)
        
    output_path = os.path.join(image_folder_path, f'{image_name}.jpg')
    image_data = image_data.split(",")[1]  # Remove the prefix of Base64 encoding if present
    image_bytes = base64.b64decode(image_data)
    
    image = pilImage.open(io.BytesIO(image_bytes))
    image = image.convert('RGB')
    image.save(output_path)
    
    return jsonify({'message': 'Image Saved Successfully.'})
    
@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json
    image_data = data['image_data']
    image_name = data["image_name"]
    image_name = re.sub(r'\s+', '_', image_name)
    format_type = data["format_type"]
    set = data["class_set"]
    username = data["username"]
    if format_type == "yolo":
        image_folder_path = os.path.join("Annotations", f"Yolo_AnnotationsSet{set}", "images")
        if not os.path.exists(os.path.join("Annotations", f"Yolo_AnnotationsSet{set}")):
            os.mkdir(os.path.join("Annotations", f"Yolo_AnnotationsSet{set}"))
        if not os.path.exists(image_folder_path):
            os.mkdir(image_folder_path)
    elif format_type == "pascal":
        image_folder_path = os.path.join("Annotations", f"PASCAL_AnnotationsSet{set}")
        if not os.path.exists(image_folder_path):
            os.mkdir(image_folder_path)
    elif format_type == 'coco':
        image_folder_path = os.path.join("Annotations", f"COCO_AnnotationsSet{set}")
        if not os.path.exists(image_folder_path):
            os.mkdir(image_folder_path)
    elif format_type == "tensorflow":
        image_name = image_name.replace(',', "_")
        image_folder_path = os.path.join("Annotations", f"Tensorflow_AnnotationsSet{set}")
        if not os.path.exists(image_folder_path):
            os.mkdir(image_folder_path)
    elif format_type == "obb":
        image_folder_path = os.path.join("Annotations", f"OrientedObject_AnnotationsSet{set}", "images")
        if not os.path.exists(os.path.join("Annotations", f"OrientedObject_AnnotationsSet{set}")):
            os.mkdir(os.path.join("Annotations", f"OrientedObject_AnnotationsSet{set}"))
        if not os.path.exists(image_folder_path):
            os.mkdir(image_folder_path)
    
    output_path = os.path.join(image_folder_path, f'{image_name}.jpg')
    
    image_data = image_data.split(",")[1] 
    image_bytes = base64.b64decode(image_data)
    
    image = pilImage.open(io.BytesIO(image_bytes))
    image = image.convert('RGB')
    image.save(output_path)
    
    # save to server
    server_image_folder_path = os.path.join("Annotations", f"Server_AnnotationsSet{set}", "images")
    if not os.path.exists(os.path.join("Annotations", f"Server_AnnotationsSet{set}")):
        os.mkdir(os.path.join("Annotations", f"Server_AnnotationsSet{set}"))
    if not os.path.exists(server_image_folder_path):
        os.mkdir(server_image_folder_path)
    image.save(os.path.join(server_image_folder_path, f'{image_name}.jpg'))
    
    with open(os.path.join("Annotations", 'log.csv'), "a") as f:
        f.write(f"{username}, {image_name}.jpg, {datetime.now()} \n")
    return jsonify({'message': 'Image Saved Successfully.'})

@app.route('/save_annotations', methods=['POST'])
def save_annotations():
    data = request.json
    image_name = data["image_name"]
    image_name = re.sub(r'\s+', '_', image_name)
    format_type = data["format_type"]
    yolo_labels = data["yolo_labels"]
    image_size = data["img_size"]
    set = data["class_set"]
    if format_type == 'yolo':
        label_folder_path = os.path.join("Annotations", f"Yolo_AnnotationsSet{set}", "labels")
        if not os.path.exists(label_folder_path):
            os.mkdir(label_folder_path)
        output_path = os.path.join(label_folder_path, f'{image_name}.txt')
        with open(output_path, 'w') as file:
            for label in yolo_labels:
                id, x, y, w, h, _ = get_values(label)
                file.write(f'{id} {x} {y} {w} {h} ' + '\n')
       
    elif format_type == 'pascal':
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
        
        writer = Writer(os.path.join(voc_folder_path, f'{image_name}.jpg'), image_size, image_size)
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
            writer.addObject(classes[set-1][id], x1, y1, x2, y2)
        writer.save(os.path.join(voc_folder_path, f'{image_name}.xml'))
        
    elif format_type == 'coco':
        coco_folder_path = os.path.join("Annotations", f"COCO_AnnotationsSet{set}")
        
        if os.path.exists(os.path.join(coco_folder_path, "annotations.json")):
            with open(os.path.join(coco_folder_path, "annotations.json"), "r") as f:
                old_annotations = json.load(f)
        else:
            with open(os.path.join("annotations_template", "annotations.json"), "r") as f:
                old_annotations = json.load(f)
        
        if os.path.exists(os.path.join(coco_folder_path, "coco_info.yaml")):
            with open(os.path.join(coco_folder_path, "coco_info.yaml"), "r") as f:
                coco_info = yaml.safe_load(f)
                MAX_IMAGE_ID = coco_info["MAX_IMAGE_ID"]
                MAX_ANNO_ID = coco_info["MAX_ANNO_ID"]
        else:
            with open(os.path.join("annotations_template", "coco_info.yaml"), "r") as f:
                coco_info = yaml.safe_load(f)
                MAX_IMAGE_ID = coco_info["MAX_IMAGE_ID"]
                MAX_ANNO_ID = coco_info["MAX_ANNO_ID"]
        MAX_IMAGE_ID += 1
        new_image_info = {
            "id": MAX_IMAGE_ID,
            "file_name": f'{image_name}.jpg',
            "width": image_size,
            "height": image_size
        }
        old_annotations["images"].append(new_image_info)
        
        new_anno_infos = []
        for label in yolo_labels:
            MAX_ANNO_ID += 1
            new_anno_info = yolo2coco(label, MAX_IMAGE_ID, MAX_ANNO_ID, image_size)
            new_anno_infos.append(new_anno_info)
        old_annotations["annotations"].extend(new_anno_infos)
        
        with open(os.path.join(coco_folder_path, "annotations.json"), "w") as f:
            json.dump(old_annotations, f)
        
        coco_info["MAX_IMAGE_ID"] = MAX_IMAGE_ID
        coco_info["MAX_ANNO_ID"] = MAX_ANNO_ID
        with open(os.path.join(coco_folder_path, "coco_info.yaml"), "w") as f:
            yaml.dump(coco_info, f)

    elif (format_type == 'tensorflow'):
        image_name = image_name.replace(',', "_")
        annotations_path = os.path.join("Annotations", f"Tensorflow_AnnotationsSet{set}")
        if not os.path.exists(os.path.join(annotations_path, "annotations.csv")):
            shutil.copy("./annotations_template/annotations.csv", annotations_path)
        new_annos = []
        for label in yolo_labels:
            new_anno = yolo2tensorflow(label, set, f'{image_name}.jpg', 480)
            new_annos.append(new_anno)
        with open(os.path.join(annotations_path, "annotations.csv"), "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(new_annos)
    elif (format_type == 'obb'):
        label_folder_path = os.path.join("Annotations", f"OrientedObject_AnnotationsSet{set}", "labels")
        if not os.path.exists(label_folder_path):
            os.mkdir(label_folder_path)
        output_path = os.path.join(label_folder_path, f'{image_name}.txt')
        with open(output_path, 'w') as file:
            for label in yolo_labels:
                id, x, y, w, h = label.values()
                file.write(f'{id} {x} {y} {w} {h} ' + '\n')

    # save to server
    label_folder_path = os.path.join("Annotations", f"Server_AnnotationsSet{set}", "labels")
    if not os.path.exists(label_folder_path):
        os.mkdir(label_folder_path)
    output_path = os.path.join(label_folder_path, f'{image_name}.txt')
    with open(output_path, 'w') as file:
        
        for label in yolo_labels:
            id, x, y, w, h, _ = get_values(label)
            file.write(f'{id} {x} {y} {w} {h} ' + '\n')
    
        writer = Writer(os.path.join("Annotations", f"Server_AnnotationsSet{set}", f'{image_name}.jpg'), image_size, image_size)
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
            writer.addObject(classes[set-1][id], x1, y1, x2, y2)
        writer.save(os.path.join(label_folder_path, f'{image_name}.xml'))
        
    return jsonify({'message': 'Success'})

def get_values(label):
    return [label["id"], label["x"], label["y"], label["w"], label["h"], "work"]

def yolo2coco(yololabels, image_id, anno_id, img_size):
    id, x, y, w, h, _ = get_values(yololabels)
    
    x *= img_size
    y *= img_size
    w *= img_size
    h *= img_size
    x1 = x - w / 2
    y1 = y - h / 2
    new_annotation = {
        "id": anno_id,
        "image_id": image_id,
        "category_id": id,
        "bbox": [x1, y1, w, h],
        "area":w*h,
        "segmentation":[],
        "iscrowd":0
    }
    return new_annotation

def yolo2tensorflow(yololabels, class_set, image_name, img_size):
    id, x, y, w, h, _ = get_values(yololabels)
    
    x *= img_size
    y *= img_size
    w *= img_size
    h *= img_size
    x1 = x - w / 2
    y1 = y - h / 2
    x2 = x + w / 2
    y2 = y + h / 2
    new_annotation = [image_name, img_size, img_size, classes[class_set][id], x1, y1, x2, y2]
    return new_annotation

@app.route('/download_annotations', methods=['GET'])
def download_annotations():
    class_set = request.args.get('class_set')
    completed_file_names = request.args.get('filenames').split(',')
    format_type = request.args.get('format_type')
    
    zip_filename = 'annotations.zip'
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for file in completed_file_names:
            filename = re.sub(r'\s+', '_', file)
            replace_chars = {"[": "", "]": "", "\"": ""}
            filename = "".join(replace_chars.get(c, c) for c in filename)
            
            if format_type == "yolo":
                image_file_path = os.path.join("./Annotations", f"Server_AnnotationsSet{class_set}", "images", f'{filename}.jpg')
                label_file_path = os.path.join("./Annotations", f"Server_AnnotationsSet{class_set}", "labels", f'{filename}.txt')

                zipf.write(image_file_path, arcname=os.path.join("images", os.path.basename(image_file_path)))
                zipf.write(label_file_path, arcname=os.path.join("labels", os.path.basename(label_file_path)))
            else:
                image_file_path = os.path.join("./Annotations", f"Server_AnnotationsSet{class_set}", "images", f'{filename}.jpg')
                label_file_path = os.path.join("./Annotations", f"Server_AnnotationsSet{class_set}", "labels", f'{filename}.xml')

                zipf.write(image_file_path, arcname=os.path.join("annotations", os.path.basename(image_file_path)))
                zipf.write(label_file_path, arcname=os.path.join("annotations", os.path.basename(label_file_path)))

    return send_file(zip_filename, as_attachment=True)

@app.route('/download_image', methods=['GET'])
def download_image():
    filename = request.args.get('filenames')
    image_name = re.sub(r'\s+', '_', filename)
    image_name = image_name.replace("\"", "")
    image_file_path = os.path.join("Annotations", f"Server_images", f'{image_name}.jpg')
    return send_file(image_file_path, as_attachment=True)

@app.route('/upload_yolo_labels', methods=['POST'])
def upload_yolo_labels():
    if 'file' not in request.files:
        return 'no labels', 400

    files = request.files.getlist('file')
    if len(files) == 0:
        return 'no labels', 400

    labels = []
    for file in files:
        if file and file.filename.endswith('.txt'):
            filename = file.filename
            # existing_image = Image.query.filter_by(filename=filename).first()
            existing_image = True
            if existing_image:
                label_data = parse_label_file(file)
                if label_data:
                    labels.append(label_data)
            else:
                return 'not found in database', 400
    return jsonify(labels)

def parse_label_file(file):
    labels = []
    annos = []
    anno_id = 0
    for line in file:
        parts = line.strip().split()
        if len(parts) == 5:
            class_id, x_center, y_center, width, height = map(float, parts)
            labels.append({
                'id': class_id, 
                'x': x_center, 
                'y': y_center, 
                'w': width, 
                'h': height, 
                'anno_id': anno_id
            })
            aug_w = width*720
            aug_h = height*720
            annos.append({
                'id': class_id, 
                'x': x_center*720 - aug_w/2, 
                'y': y_center*720 - aug_h/2,
                'w': aug_w, 
                'h': aug_h, 
                'anno_id': anno_id
            })
            anno_id += 1
    
    filename = file.filename[:-4]
    return {'filename': filename, 'labels': labels, 'annos': annos, 'anno_id': anno_id} if labels else None

if __name__ == '__main__':
    if not os.path.exists("./Annotations"): 
        os.mkdir("./Annotations")
        
    app.run(host='0.0.0.0', port=8000, debug=True)