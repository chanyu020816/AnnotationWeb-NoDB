import math
import os

import cv2
from tqdm import tqdm


def tile_to_lonlat(x_tile, y_tile, zoom_level):
    n = 2.0**zoom_level
    lon_degree = x_tile / n * 360.0 - 180.0
    lat_radian = math.atan(math.sinh(math.pi * (1 - 2 * y_tile / n)))
    lat_degree = math.degrees(lat_radian)

    return lat_degree, lon_degree


def read_label(label_path):
    labels = []

    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            class_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])
            labels.append([class_id, x, y, w, h])

    return labels


def labels_to_lonlat(labels, img_x_tile, img_y_tile, zoom_level):
    label_lonlat_coords = []

    for class_id, x, y, w, h in labels:
        x_tile = img_x_tile + x
        y_tile = img_y_tile + y
        label_lat, label_lon = tile_to_lonlat(x_tile, y_tile, zoom_level)
        label_lonlat_coord = [class_id, label_lon, label_lat, w, h]
        label_lonlat_coords.append(label_lonlat_coord)

    return label_lonlat_coords


def transform_WMTS_labels(WMTS_label_path):
    WMTS_label_filename = os.path.basename(WMTS_label_path)
    year = int(WMTS_label_filename.split("-")[0])
    zoom_level = int(WMTS_label_filename.split("-")[1])
    img_x_tile = int(WMTS_label_filename.split("-")[2])
    img_y_tile = int(WMTS_label_filename.split("-")[3][:-4])

    labels = read_label(WMTS_label_path)
    label_lonlat_coords = labels_to_lonlat(labels, img_x_tile, img_y_tile, zoom_level)

    labels_output_path = WMTS_label_path[:-4] + "lonlat.txt"

    with open(labels_output_path, "w") as f:
        for lonlat_label in label_lonlat_coords:
            f.write(
                f"{lonlat_label[0]} {lonlat_label[1]} {lonlat_label[2]} {lonlat_label[3]} {lonlat_label[4]}\n"
            )

    return


def remove_padding(img, target_size):
    img_height, img_width = img.shape[:2]

    start_x = (img_width - target_size) // 2
    start_y = (img_height - target_size) // 2

    cropped_img = img[start_y : start_y + target_size, start_x : start_x + target_size]

    return cropped_img


def modify_labels(labels, img_size, target_size):
    new_labels = []

    for label in labels:
        new_x = (label[1] * img_size - (img_size - target_size) // 2) / target_size
        new_y = (label[2] * img_size - (img_size - target_size) // 2) / target_size
        new_w = label[3] * img_size / target_size
        new_h = label[4] * img_size / target_size

        new_label = [label[0], new_x, new_y, new_w, new_h]
        new_labels.append(new_label)

    return new_labels


if __name__ == "__main__":
    image_folder = "../../../data/padded_WMTS/images"
    label_folder = "../../../data/padded_WMTS/labels"
    save_folder = "../../../data/rmPadded_WMTS/"
    target_size = 256

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        os.makedirs(os.path.join(save_folder, "images"))
        os.makedirs(os.path.join(save_folder, "labels"))

    image_files = os.listdir(image_folder)

    for image_file in tqdm(image_files):
        if image_file.endswith(".jpg") or image_file.endswith(".png"):
            label_filename = f"{image_file.split('.')[0]}.txt"
            label_file = os.path.join(label_folder, label_filename)
            if not os.path.exists(label_file):
                print(label_file)
                continue

            image = cv2.imread(os.path.join(image_folder, image_file))
            labels = read_label(label_file)
            new_image = remove_padding(image, target_size)

            image_save_filename = image_file.replace("_padded", "")
            label_save_filename = label_filename.replace("_padded", "")

            cv2.imwrite(
                os.path.join(save_folder, "images", image_save_filename), new_image
            )
            img_size = image.shape[0]
            new_labels = modify_labels(labels, img_size, target_size)

            with open(
                os.path.join(save_folder, "labels", label_save_filename), "w"
            ) as f:
                for label in new_labels:
                    f.write(f"{label[0]} {label[1]} {label[2]} {label[3]} {label[4]}\n")
            transform_WMTS_labels(
                os.path.join(save_folder, "labels", label_save_filename)
            )
