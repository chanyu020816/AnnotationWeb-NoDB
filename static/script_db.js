let images = [];
let imagesName = [];
let currentImageIndex = 0;
let menuItemsCompleted = [];
let completedImageName = [];
let labels = [];
let prev_index = -1;
let change = false;
let detections = [];
let paddings = [];
let ptype = 1;
let type = "label";
let classSet = 1; // 1: 1904, 2: 1921
let annotations = [];
let parentImagesName = [];
let format_type = "yolo";
let mode = "annotate";
let anno_ids = [];
const split_size = 480;
const container_size = 720;
const classColors = {
  0: "red",
  1: "blue",
  2: "green",
  3: "purple",
  4: "orange",
  5: "pink",
  6: "yellow",
  7: "cyan",
  8: "magenta",
  9: "teal",
  10: "brown",
  11: "olive",
  12: "navy",
  13: "lime",
  14: "coral",
  15: "aqua",
  16: "maroon",
  17: "lavender",
  18: "grey",
  19: "gold",
  20: "silver",
  21: "indigo",
};

window.onload = function () {
  const username = localStorage.getItem("username");
  const isLogin = localStorage.getItem("isLogin");
  const login_setting = localStorage.getItem("login_setting");

  if (isLogin) {
    const formContainer = document.getElementById("form_container");
    const content = document.querySelector(".content");
    const nav = document.querySelector("nav");

    if (formContainer) formContainer.style.display = "none";
    if (content) content.style.display = "block";
    if (nav) nav.style.display = "block";

    [type, classSet, mode] = get_login_set_mode(login_setting);

    const liItems = document.querySelectorAll("li");
    liItems.forEach((li) => {
      li.classList.add("modify");
      li.addEventListener("click", function () {
        ptype = parseInt(this.getAttribute("data-ptype"));
        liItems.forEach((item) => {
          /website/;
          if (item === this) {
            item.classList.add("ptype", "active");
            const aElement = item.querySelector("a");
            if (aElement) {
              // aElement.style.border = "3px solid red";
              aElement.style.outline = "3px solid red";
              aElement.style.outlineOffset = "-3px";
            }
          } else {
            item.classList.remove("ptype", "active");
            const aElement = item.querySelector("a");
            if (aElement) {
              aElement.style.outline = "none";
            }
          }
        });
      });
    });

    // 修改模式下，會多一個上傳標註檔案的按鈕
    if (mode === "modify" && localStorage.getItem("page") !== "WMTSlabel") {
      document.getElementById("upload-label-button").style.display = "block";
    } else {
      document.getElementById("upload-label-button").style.display = "none";
    }
    if (localStorage.getItem("page") !== "WMTSlabel") {
      document.getElementById("image-menu").style.top = "360px";
    }
  }
};

function get_login_set_mode(login_setting) {
  const text = login_setting.split("_");
  const type = text[0];
  const class_set = (text[1] === "1921") + 1; // -> 1: 1904, 2: 1921
  const mode = text[2];

  return [type, class_set, mode];
}

function get_url_location() {
  const url = window.location.href.split("/");
  return url[url.length - 1];
}

function displayPagination() {
  console.log("qwerunxk");
  document.getElementById("pagination1_1").style.top = `${800}px`;
  document.getElementById("pagination1_2").style.top = `${950}px`;

  if (document.getElementById("pagination1_3")) {
    document.getElementById("pagination1_3").style.top = `${1100}px`;
  }
  if (document.getElementById("pagination1_4")) {
    document.getElementById("pagination1_4").style.top = `${1250}px`;
  }
  if (document.getElementById("pagination1_5")) {
    document.getElementById("pagination1_5").style.top = `${1400}px`;
  }
  if (document.getElementById("pagination1_6")) {
    document.getElementById("pagination1_6").style.top = `${1550}px`;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  if (document.getElementById("pagination1_1")) {
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.type = "text/css";
    link.href = "static/pagination.css";
    document.head.appendChild(link);
  }
  const wmts_tile_Button = document.getElementById("crawler-tile-button");
  if (wmts_tile_Button)
    wmts_tile_Button.addEventListener("click", downloadWTMSImage_by_tile);

  const wmts_lonlat_Button = document.getElementById("crawler-lonlat-button");
  if (wmts_lonlat_Button)
    wmts_lonlat_Button.addEventListener("click", downloadWTMSImage_by_lonlat);

  document
    .getElementById("upload-button")
    .addEventListener("click", function () {
      document.getElementById("file-input").click();
    });
  document
    .getElementById("file-input")
    .addEventListener("change", handleFileSelect);
  document
    .getElementById("upload-label-button")
    .addEventListener("click", function () {
      document.getElementById("label-input").click();
    });
  document
    .getElementById("label-input")
    .addEventListener("change", handleLabelSelect);
  document
    .getElementById("prev-button")
    .addEventListener("click", showPrevImage);
  document
    .getElementById("next-button")
    .addEventListener("click", showNextImage);
  document.getElementById("reset-button").addEventListener("click", labelreset);
  const ptypeBtns = document.querySelectorAll(".ptypeBtn");

  document
    .getElementById("complete-button")
    .addEventListener("click", async function () {
      if (!completedImageName.includes(imagesName[currentImageIndex])) {
        completedImageName.push(imagesName[currentImageIndex]);
      }
      menuItemsCompleted.push(currentImageIndex);
      markImageAsCompleted(currentImageIndex);
      complete_label_image();
    });

  document
    .getElementById("download-button")
    .addEventListener("click", async function () {
      const page = localStorage.getItem("page");
      if (page == "WMTSlabel") {
        download_labeled_WMTSimages();
      } else {
        download_labeled_images();
      }
    });

  const formatSelect = document.getElementById("format-select");
  formatSelect.addEventListener("change", function () {
    format_type = formatSelect.value;
  });

  const logoutBtn = document.getElementById("logout-button");
  logoutBtn.addEventListener("click", logout);
});

async function fetchFilesFromServer(x_tile, y_tile, zoom, year) {
  const response = await fetch("/website/download_wmts_image", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ x_tile, y_tile, zoom, year }),
  });

  const data = await response.json();
  if (data.message === "Success") {
    const files = data.files.map((file) => {
      const byteCharacters = atob(file.content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: file.type });
      return new File([blob], file.name, { type: file.type });
    });
    return files;
  } else {
    document.getElementById("download-status").textContent =
      "網站目前無法抓取圖片資料";
    throw new Error("Failed to download images");
  }
}

async function downloadWTMSImage_by_lonlat() {
  document.getElementById("download-status").textContent = "正在下載該區域圖片";
  var lon = document.getElementById("label-lon-input").value;
  var lat = document.getElementById("label-lat-input").value;
  var zoom = document.getElementById("label-zoom-input").value;
  lon = parseFloat(lon);
  lat = parseFloat(lat);
  zoom = parseInt(zoom);
  var year = 1904;
  if (classSet === 2) {
    year = 1920;
  }
  const tile = lonlatToTile(lon, lat, zoom);
  const x_tile = tile["x"];
  const y_tile = tile["y"];
  document.getElementById("label-xtile-input").value = x_tile;
  document.getElementById("label-ytile-input").value = y_tile;

  const files = await fetchFilesFromServer(x_tile, y_tile, zoom, year);
  if (files.length === 0) {
    document.getElementById("download-status").textContent =
      "該位置周圍沒有圖片";
  } else {
    document.getElementById("download-status").textContent = "";
  }

  const promises = files
    .filter((f) => f.type.match("image.*"))
    .map((f) => readFileAsDataURL(f));
  const imageContainer = document.getElementById("image-container");
  imageContainer.addEventListener("mouseover", imageMouseOverHandler);
  imageContainer.addEventListener("mouseout", imageMouseOutHandler);
  Promise.all(promises).then((results) => console.log(results));
}

async function downloadWTMSImage_by_tile() {
  document.getElementById("download-status").textContent = "正在下載該區域圖片";
  var x_tile = document.getElementById("label-xtile-input").value;
  var y_tile = document.getElementById("label-ytile-input").value;
  var zoom = document.getElementById("label-zoom-input").value;
  x_tile = parseFloat(x_tile);
  y_tile = parseFloat(y_tile);
  zoom = parseInt(zoom);
  var year = 1904;
  if (classSet === 2) {
    year = 1920;
  }
  const lonlat = tileToLonLat(x_tile, y_tile, zoom);
  document.getElementById("label-lon-input").value = lonlat["lon"].toFixed(2);
  document.getElementById("label-lat-input").value = lonlat["lat"].toFixed(2);

  const files = await fetchFilesFromServer(x_tile, y_tile, zoom, year);

  if (files.length === 0) {
    document.getElementById("download-status").textContent =
      "該位置周圍沒有圖片";
  } else {
    document.getElementById("download-status").textContent = "";
  }
  const promises = files
    .filter((f) => f.type.match("image.*"))
    .map((f) => readFileAsDataURL(f));
  const imageContainer = document.getElementById("image-container");
  imageContainer.addEventListener("mouseover", imageMouseOverHandler);
  imageContainer.addEventListener("mouseout", imageMouseOutHandler);

  Promise.all(promises).then((results) => console.log(results));
}

function lonlatToTile(lon, lat, zoomLevel) {
  var latRadian = lat * (Math.PI / 180);
  var n = Math.pow(2, zoomLevel);
  var xTile = Math.floor(((lon + 180) / 360) * n);
  var yTile = Math.floor(
    ((1 - Math.log(Math.tan(latRadian) + 1 / Math.cos(latRadian)) / Math.PI) /
      2) *
      n,
  );
  return { x: xTile, y: yTile };
}

function tileToLonLat(x_tile, y_tile, zoomLevel) {
  x_tile += 0.5;
  y_tile += 0.5;
  const n = Math.pow(2.0, zoomLevel);
  const lon_degree = (x_tile / n) * 360.0 - 180.0;
  const lat_radian = Math.atan(Math.sinh(Math.PI * (1 - (2 * y_tile) / n)));
  const lat_degree = lat_radian * (180.0 / Math.PI);

  return { lat: lat_degree, lon: lon_degree };
}

function handleFileSelect(event) {
  const downloadStatus = document.getElementById("download-status");
  downloadStatus.textContent = "圖片上傳中";
  let files = Array.from(event.target.files);
  if (!files || files.length === 0) return;

  if (images.length >= 100) {
    alert("已達到圖片上限 無法繼續上傳，請先完成目前圖片標註！");
    return;
  }

  const promises = files
    .filter((f) => f.type.match("image.*"))
    .map((f) => readFileAsDataURL(f));
  const imageContainer = document.getElementById("image-container");
  imageContainer.addEventListener("mouseover", imageMouseOverHandler);
  imageContainer.addEventListener("mouseout", imageMouseOutHandler);
  setTimeout(() => {
    downloadStatus.textContent = "已完成圖片上傳";
  }, 10000);
  setTimeout(() => {
    downloadStatus.textContent = "";
  }, 5000);
}

function readFileAsDataURL(file) {
  return new Promise((reject) => {
    const reader = new FileReader();
    reader.onload = function (event) {
      const img = new Image();
      img.onload = function () {
        // avoid repeat uploading
        if (
          parentImagesName.indexOf(
            file.name.split(".").slice(0, -1).join("."),
          ) === -1
        ) {
          const [newImages, newImageNames] = splitImage(
            img,
            file,
            split_size,
            mode,
          );
          images.push(...newImages);
          imagesName.push(...newImageNames);
          updateImageMenu(imagesName);
          showImage(currentImageIndex, (change = false));
        }
      };
      img.src = event.target.result;
    };
    reader.onerror = (error) => reject(error);
    reader.readAsDataURL(file);
  });
}

async function handleLabelSelect(event) {
  let files = Array.from(event.target.files);
  if (!files || files.length === 0) {
    console.error("未选择文件");
    return;
  }
  const promises = files
    .filter((f) => f.type.match("text/plain"))
    .map((f) => readLabel(f));
}

async function readLabel(file) {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await fetch("/website/upload_yolo_labels", {
      method: "POST",
      body: formData,
    });
    if (response.ok) {
      const labels_data = await response.json();
      if (labels_data !== null) {
        const index = imagesName.indexOf(labels_data[0].filename);

        if (index !== -1) {
          anno_ids[index] = labels_data[0].anno_id;
          annotations[index] = labels_data[0].annos;
          labels[index] = labels_data[0].labels;
          // showImage(currentImageIndex, modify=true);
        } else {
          console.log(labels_data[0].filename, ".jpg not uploaded");
        }
      } else {
        console.log(labels_data[0].filename, ".txt has no label");
      }
    } else {
      console.error("上传失败:", response.statusText);
    }
  } catch (error) {
    console.error("上传时出错:", error);
  }
  showImage(currentImageIndex, (modify = true));
}

function showImage(index, change = true, modify = false) {
  const container = document.getElementById("image-container");
  const imageDisplay = document.getElementById("image_display");
  if (imageDisplay) {
    container.removeChild(imageDisplay);
  }

  const img = document.createElement("img");
  img.id = "image_display";
  img.src = images[index];
  container.appendChild(img);

  updateAnnotations(index);
  const menuItems = document.querySelectorAll("#image-menu li");
  menuItems.forEach((menuItem, menuItemIndex) => {
    const link = menuItem.querySelector("a");
    if (menuItemIndex === index) {
      link.style.color = "blue";
      link.style.textDecoration = "underline";
    } else {
      link.style.color = "black";
      link.style.textDecoration = "underline";
    }
  });
  document
    .getElementById("image_display")
    .addEventListener("click", imageClickHandler);
  updateImageCounter(currentImageIndex);
  updatCompleteCounter();
  updateLabelCounter(currentImageIndex);
}

function updateLabelCounter(index) {
  document.getElementById("label-counter").textContent =
    "標註框數量 " + labels[index].length;
}

function updateAnnotations(index) {
  // 獲取指定索引的圖片的標註結果
  const currentImageAnnotations = annotations[index];
  if (!currentImageAnnotations) {
    return; // 如果沒有標註結果，則返回
  }

  // 移除上一個圖片的標註
  const imageContainer = document.getElementById("image-container");
  const divs = imageContainer.getElementsByClassName("overlay-div");
  while (divs.length > 0) {
    divs[0].parentNode.removeChild(divs[0]);
  }

  // 顯示當前圖片的標註
  currentImageAnnotations.forEach((annotation) => {
    const { id, x, y, w, h, anno_id } = annotation;
    const rect = document.createElement("div");
    rect.className = "overlay-div";
    rect.style.position = "absolute";
    rect.style.left = `${x}px`;
    rect.style.top = `${y}px`;
    rect.style.width = `${w}px`;
    rect.style.height = `${h}px`;
    rect.style.backgroundColor = classColors[id];
    rect.style.opacity = "0.5";
    rect.dataset.anno_id = anno_id;
    imageContainer.appendChild(rect);

    rect.addEventListener("click", function () {
      const removedAnnoId = this.dataset.anno_id;
      labels[currentImageIndex] = labels[currentImageIndex].filter(
        (label) => parseInt(label.anno_id) !== parseInt(removedAnnoId),
      );
      annotations[currentImageIndex] = annotations[currentImageIndex].filter(
        (anno) => parseInt(anno.anno_id) !== parseInt(removedAnnoId),
      );
      this.remove();
      updateLabelCounter(currentImageIndex);
    });
  });
}

function showPrevImage() {
  if (currentImageIndex > 0) {
    currentImageIndex--;
    showImage(currentImageIndex);
  }
}

function showNextImage() {
  if (currentImageIndex < images.length - 1) {
    currentImageIndex++;
    showImage(currentImageIndex);
  }
}

function updateImageMenu(imageNames) {
  document.getElementById("image-menu").style.display = "block";
  const menu = document.getElementById("image-menu");
  menu.innerHTML = ""; // 清空菜单内容
  // 为每张图像创建菜单项
  if (imageNames.length !== 0) {
    imageNames.forEach((name, index) => {
      const menuItem = document.createElement("li");
      menuItem.id = `menu-item-${index}`;

      // 添加超链接元素
      const link = document.createElement("a");
      link.textContent = name; // 使用图像名称作为超链接文本内容
      link.href = "#"; // 链接地址设为 #
      link.addEventListener("click", (event) => {
        event.preventDefault(); // 阻止默认点击事件
        if (images.length === 0) {
          showBlankImage();
        } else {
          currentImageIndex = index;
          showImage(index);
        }
      });
      menuItem.appendChild(link);

      const downloadButtonContainer = document.createElement("div"); // 创建一个新的容器元素
      downloadButtonContainer.style.display = "inline-block"; // 设置容器为内联块级元素

      // download-button
      const downloadButton = document.createElement("button");
      downloadButton.textContent = "下載圖片";
      downloadButton.className = "download-image-button";

      downloadButton.addEventListener("click", async function () {
        downloadImage(index);
      });

      downloadButtonContainer.appendChild(downloadButton); // 将 download button 放入容器内
      menuItem.appendChild(downloadButtonContainer); // 将容器放入菜单项内

      // 添加勾选框
      const checkbox = document.createElement("span");
      checkbox.className = "checkbox";
      menuItem.appendChild(checkbox);
      // 检查图像是否已完成，如果是，则添加 completed 类
      if (menuItemsCompleted.includes(index)) {
        menuItem.classList.add("completed");
      }
      menu.appendChild(menuItem);
    });

    // 标记当前图像的菜单项
    const currentMenuItem = document.getElementById(
      `menu-item-${currentImageIndex}`,
    );
    if (currentMenuItem) {
      // 将当前图像的菜单项设置为蓝色字体并添加下划线
      currentMenuItem.querySelector("a").style.color = "blue";
      currentMenuItem.querySelector("a").style.textDecoration = "underline";
    }
  }
}

async function complete_label_image() {
  const downloadStatus = document.getElementById("download-status");
  if (images[currentImageIndex]) {
    const imageData = images[currentImageIndex];
    const imageName = imagesName[currentImageIndex];
    const label = labels[currentImageIndex];

    try {
      downloadStatus.textContent = `正在儲存 ${imageName} ...`;
      await fetch("/website/save_image", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image_data: imageData,
          image_name: imageName,
          format_type: format_type,
          class_set: classSet,
          username: localStorage.getItem("username"),
        }),
      });
      await fetch("/website/save_annotations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image_name: imageName,
          format_type: format_type,
          yolo_labels: label,
          img_size: split_size,
          class_set: classSet,
          username: localStorage.getItem("username"),
        }),
      });
      await fetch("/website/add_labels_db", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: localStorage.getItem("username"),
          image_name: imageName,
          yolo_labels: label,
          class_set: classSet,
        }),
      });
      downloadStatus.textContent = "標註成功!";
      setTimeout(() => {
        downloadStatus.textContent = "";
      }, 10000);
    } catch (error) {
      console.error("error: ", error);
      downloadStatus.textContent = "";
    }
  } else {
    downloadStatus.textContent = "沒有圖片可以標註.";
  }
}

function splitImage(image, file, size, mode) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  const numH = Math.ceil(image.height / size);
  const numW = Math.ceil(image.width / size);
  const newH = numH * size;
  const newW = numW * size;
  const padH = Math.ceil((newH - image.height) / 2);
  const padW = Math.ceil((newW - image.width) / 2);

  const parentImage = {
    name: file.name,
    width: image.width,
    height: image.height,
    split_size: size,
  };
  const childImages = [];
  canvas.height = newH;
  canvas.width = newW;
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, newW, newH);
  ctx.drawImage(
    image,
    0,
    0,
    image.width,
    image.height,
    padW,
    padH,
    image.width,
    image.height,
  );
  const images = [];
  const imageNames = [];

  const fileName = file.name.split(".").slice(0, -1).join(".");
  parentImagesName.push(fileName);

  for (let h = 0; h < numH; h++) {
    for (let w = 0; w < numW; w++) {
      const cut_canvas = document.createElement("canvas");
      const cut_ctx = cut_canvas.getContext("2d");
      cut_canvas.width = size;
      cut_canvas.height = size;
      cut_ctx.drawImage(
        canvas,
        w * size,
        h * size,
        size,
        size,
        0,
        0,
        size,
        size,
      );
      const imageDataURL = cut_canvas.toDataURL();
      images.push(imageDataURL);
      const imageName = `${fileName}_h${h}_w${w}`;
      imageNames.push(imageName);
      detections.push([]);
      labels.push([]);
      annotations.push([]);
      anno_ids.push(0);
      const padding = createPadding(h, w, numH, numW, size, padH, padW);
      paddings.push([padding]);
      child_img = {
        name: imageName,
        location: [h, w],
        paddings: padding,
      };
      childImages.push(child_img);
    }
  }
  if (mode === "modify") {
    if ((image.height === 480) & (image.width === 480)) {
      return [[canvas.toDataURL()], [fileName]];
    } else {
      console.error("image size wrong");
    }
  } else if (localStorage.getItem("page") === "WMTSlabel") {
    image = {
      name: file.name.split(".")[0],
      location: [0, 0],
      paddings: [112, 112, 368, 368], // WMTS images are 256 * 256
    };
    add_parent_child_images(parentImage, [image]);
    return [[canvas.toDataURL()], [fileName]];
  }
  add_parent_child_images(parentImage, childImages);
  return [images, imageNames];
}

function add_parent_child_images(parentImage, childImages) {
  const data = {
    username: localStorage.getItem("username"),
    parent_image: parentImage,
    child_images: childImages,
  };

  fetch("/website/add_img_db", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .catch((error) => {
      console.error("There was a problem with your fetch operation:", error);
    });
}

function download_labeled_images() {
  const downloadStatus = document.getElementById("download-status");
  if (completedImageName.length > 0) {
    const queryString = `?class_set=${encodeURIComponent(
      classSet,
    )}&filenames=${encodeURIComponent(
      JSON.stringify(completedImageName),
    )}&format_type=${encodeURIComponent(format_type)}`;
    fetch(`/website/download_annotations${queryString}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        // 根据响应状态码检查下载状态
        if (response.ok) {
          // 创建一个 <a> 元素来触发下载
          const link = document.createElement("a");
          link.href = response.url;
          link.download = "annotations.zip";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } else {
          downloadStatus.textContent = "下载失败，请重试.";
        }
      })
      .catch((error) => {
        console.error("发送请求时出错:", error);
        downloadStatus.textContent = "下载失败，请重试.";
      });
  } else {
    downloadStatus.textContent = "No image completed";
  }
}

function download_labeled_WMTSimages() {
  const downloadStatus = document.getElementById("download-status");
  if (completedImageName.length > 0) {
    const queryString = `?class_set=${encodeURIComponent(
      classSet,
    )}&filenames=${encodeURIComponent(
      JSON.stringify(completedImageName),
    )}&format_type=${encodeURIComponent(format_type)}`;
    fetch(`/website/download_WMTSannotations${queryString}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        // 根据响应状态码检查下载状态
        if (response.ok) {
          // 创建一个 <a> 元素来触发下载
          const link = document.createElement("a");
          link.href = response.url;
          link.download = "annotations.zip";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } else {
          downloadStatus.textContent = "下载失败，请重试.";
        }
      })
      .catch((error) => {
        console.error("发送请求时出错:", error);
        downloadStatus.textContent = "下载失败，请重试.";
      });
  } else {
    downloadStatus.textContent = "No image completed";
  }
}

async function downloadImage(index) {
  const menuItem = document.getElementById(`menu-item-${index}`);
  if (!menuItem) return;
  const imageData = images[index];
  const imageName = imagesName[index];
  const downloadImageName = imageName.replace(/\s+/g, "_");
  try {
    await fetch("/website/save_image_for_download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_data: imageData,
        image_name: imageName,
      }),
    });

    // 下载图片
    const queryString = `?filenames=${encodeURIComponent(
      JSON.stringify(downloadImageName),
    )}`;
    const response = await fetch(`/website/download_image${queryString}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      // 创建一个 <a> 元素来触发下载
      const link = document.createElement("a");
      link.href = url;
      link.download = downloadImageName + ".jpg";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // 释放对象 URL
      window.URL.revokeObjectURL(url);
    } else {
      // 处理下载失败情况
      console.error("下载失败:", response.statusText);
    }
  } catch (error) {
    console.error("发送请求时出错:", error);
  }
}

async function openFolderDialog() {
  const options = {
    // 只允许选择文件夹
    type: "openDirectory",
  };
  // 使用浏览器提供的API打开文件对话框
  const folderHandle = await window.showDirectoryPicker(options);
  // 返回用户选择的文件夹路径
  return folderHandle;
}

function logout() {
  fetch("/website/logout", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (response.ok) {
        // 清除 LocalStorage
        removeLocalStorage();
        resetUserDatas();
        // 重新導向到登入頁面
        window.location.href = "/";
      } else {
        console.error("Failed to log out");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function removeLocalStorage() {
  localStorage.removeItem("username");
  localStorage.removeItem("isLogin");
  localStorage.removeItem("login_set");
  localStorage.removeItem("login_mode");
}

function resetUserDatas() {
  classSet = 1;
  mode = "annotate";
  images = [];
  imagesName = [];
  currentImageIndex = 0;
  menuItemsCompleted = [];
  completedImageName = [];
  parentImagesName = [];
  labels = [];
  annotations = [];
  prev_index = -1;
  detections = [];
  paddings = [];
  document.getElementById("image-counter").textContent = "圖片數量 0 / 0";
  document.getElementById("complete-counter").textContent =
    "完成標註數量 0 / 0";
  updateImageMenu(imagesName);
  const container = document.getElementById("image-container");
  const imageDisplay = document.getElementById("image_display");
  if (imageDisplay) {
    container.removeChild(imageDisplay);
  }
  const divs = container.getElementsByClassName("overlay-div");
  while (divs.length > 0) {
    divs[0].parentNode.removeChild(divs[0]);
  }
}
