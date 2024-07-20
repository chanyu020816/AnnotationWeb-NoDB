import argparse
import csv
import os

# 讀取CSV檔案
csv_file = "data.csv"


def create_nav_file(csv_file: str, templates_folder: str = "./templates"):
    """
    Create Navigation file according to the csv file
    Args:
        csv_file (str): path to the csv file (csv file have two columns, class_name, and corresponding image's path )
        templates_folder (str): relative path to templates_folder
    """

    items = []
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            items.append(row)

    html_content = """
    <nav aria-label="Page navigation">
    """

    for i in range(0, len(items), 4):
        html_content += '  <ul class="pagination">\n'
        for j in range(i, min(i + 4, len(items))):
            item = items[j]
            name = item["name"]
            image = item["image"]
            ptype = j + 1
            active_class = ' class="ptype active"' if j == 0 else ' class="ptype"'

            html_content += f"""
        <li{active_class} data-ptype="{ptype}">
        <a class="ptypeBtn" data-ptype="{ptype}" href="#" style="display: inline-block">
            {name}
            <img src="{image}" alt="圖片" />
        </a>
        </li>
    """
        html_content += "  </ul>\n"

    html_content += """
    </nav>
    """

    html_file_name = os.path.basename(csv_file).split(".")[0]
    html_file_path = os.path.join(templates_folder, html_file_name)
    with open(html_file_path, mode="w", encoding="utf-8") as file:
        file.write(html_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
