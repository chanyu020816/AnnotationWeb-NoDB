import os

import numpy as np
from PIL import Image as pilImage

from config import *
from utils.WMTS_utils import modify_labels, remove_padding


def create_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return


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


def get_values(label):
    return [label["id"], label["x"], label["y"], label["w"], label["h"], "work"]


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
