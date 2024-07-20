# import cv2
import math
import os
import time
from io import BytesIO

import numpy as np
import requests
from PIL import Image
from tqdm import tqdm

YEAR_TYPE = ["JM20K_1904", "JM50K_1920"]
URL_PREFIX = "https://gis.sinica.edu.tw/tileserver/file-exists.php?img="


def download_WMTS_image(url):
    response = requests.get(url)

    if response.status_code == 200:
        image_bytes = BytesIO(response.content)
        image = Image.open(image_bytes)

        return image
    else:
        print(f"Failed to retrieve the image. Status code: {response.status_code}")


def is_blank_WMTS_image(image) -> bool:
    """
    return True if the image is blank
    """
    image_array = np.array(image.convert("RGB"))
    blank_array = np.array([255, 255, 255], dtype=np.uint8)
    return np.all(image_array == blank_array)


def is_black_WMTS_image(image) -> bool:
    """
    return True if the image is blank
    """
    image_array = np.array(image.convert("RGB"))
    blank_array = np.array([0, 0, 0], dtype=np.uint8)
    return np.all(image_array == blank_array)


def lonlat_to_tile(lon, lat, zoom_level):
    lat_radian = math.radians(lat)
    n = 2.0**zoom_level
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int(
        (1.0 - math.log(math.tan(lat_radian) + (1 / math.cos(lat_radian))) / math.pi)
        / 2.0
        * n
    )
    return x_tile, y_tile


def get_WMTS_url(xtile: int, ytile: int, zoom_level: int = 16, year: int = 1904):
    year_type = YEAR_TYPE[year == 1920]
    img_type = "jpg" if year == 1904 else "png"

    return URL_PREFIX + year_type + f"-{img_type}-{zoom_level}-{xtile}-{ytile}"


def download_all_WMTS_images(save_folder, zoom_level: int = 16, year: int = 1904):
    if not os.path.isdir(save_folder):
        os.mkdir(save_folder)

    lon_start = 120.1062
    lat_start = 21.9430
    lon_end = 122.0564
    lat_end = 25.4814

    x_tile_start, y_tile_end = lonlat_to_tile(lon_start, lat_start, zoom_level)
    x_tile_end, y_tile_start = lonlat_to_tile(lon_end, lat_end, zoom_level)
    download_WMTS_images(
        save_folder,
        x_tile_start,
        x_tile_end,
        y_tile_start,
        y_tile_end,
        zoom_level,
        year,
    )


def download_WMTS_images(
    save_folder,
    x_tile_start,
    x_tile_end,
    y_tile_start,
    y_tile_end,
    zoom_level: int = 16,
    year: int = 1904,
):
    print("Start downloading images... ")
    i = 0
    j = 0

    for xtile in range(x_tile_start, x_tile_end):
        for ytile in range(y_tile_start, y_tile_end):
            wmts_url = get_WMTS_url(xtile, ytile, zoom_level, year)
            image = download_WMTS_image(wmts_url)

            if is_blank_WMTS_image(image):
                # print(f"WMTS image {xtile}-{ytile} is blank")
                j += 1
                continue
            if is_black_WMTS_image(image):
                # print(f"WMTS image {xtile}-{ytile} is black")
                j += 1
                continue

            if image.mode == "RGBA":
                image = image.convert("RGB")

            image.save(
                os.path.join(save_folder, f"{year}-{zoom_level}-{xtile}-{ytile}.jpg")
            )
            i += 1
            if i % 20 == 0:
                time.sleep(1)
    print(f"Downloaded {i} images, skip {j} blank images")


def get_surrounding_tile_range(x_tile, y_tile):
    x_tile_start = x_tile - 1
    x_tile_end = x_tile + 1
    y_tile_start = y_tile - 1
    y_tile_end = y_tile + 1
    return x_tile_start, x_tile_end, y_tile_start, y_tile_end


if __name__ == "__main__":
    x_tile, y_tile = lonlat_to_tile(121.5, 23.5, 16)
    x_tile_start, x_tile_end, y_tile_start, y_tile_end = get_surrounding_tile_range(
        x_tile, y_tile
    )

    print(x_tile_start, x_tile_end, y_tile_start, y_tile_end)
    save_folder = "./Test"
    # if not os.path.isdir(save_folder):
    #     os.mkdir(save_folder)
    # download_all_WMTS_images(save_folder=save_folder, zoom_level=10, year=1904)
    download_WMTS_images(
        save_folder=save_folder,
        x_tile_start=x_tile_start,
        x_tile_end=x_tile_end + 1,
        y_tile_start=y_tile_start,
        y_tile_end=y_tile_end + 1,
        zoom_level=16,
        year=1904,
    )
