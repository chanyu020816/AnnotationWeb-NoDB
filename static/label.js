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
      // childImages.push(child_img)
    }
  }
  if (mode === "modify") {
    if ((image.height === 480) & (image.width === 480)) {
      return [[canvas.toDataURL()], [fileName]];
    } else {
      console.error("image size wrong");
    }
  } else if (localStorage.getItem("page") === "WMTSlabel") {
    return [[canvas.toDataURL()], [fileName]];
  }
  add_parent_child_images(parentImage, childImages);
  return [images, imageNames];
}

function createPadding(h, w, numH, numW, size, padH, padW) {
  /*
    type (x, y -> px, py):
        0: >, >
        1: <, >
        2: >, <
        3: <, <
    */
  let padxmin = -1;
  let padymin = -1;
  let padxmax = -1;
  let padymax = -1;
  if ((numH === 1) | (numW === 1)) {
    if (numH === 1) {
      if (numW === 1) {
        // num H = 1, numW = 1
        padxmin = padW;
        padymin = padH;
        padxmax = size - padW;
        padymax = size - padH;
      } else {
        // num H = 1, numW = n
        if (w === 0) {
          padxmin = padW;
          padymin = padH;
          padxmax = size;
          padymax = size - padH;
        } else if (w === numW - 1) {
          padxmin = 0;
          padymin = padH;
          padxmax = size - padW;
          padymax = size - padH;
        } else {
          padxmin = 0;
          padymin = padH;
          padxmax = size;
          padymax = size - padH;
        }
      }
    } else {
      // num H = n, numW = 1
      if (h === 0) {
        padxmin = padW;
        padymin = padH;
        padxmax = size - padW;
        padymax = size;
      } else if (h === numH - 1) {
        padxmin = padW;
        padymin = 0;
        padxmax = size - padW;
        padymax = size - padH;
      } else {
        padxmin = padW;
        padymin = 0;
        padxmax = size - padW;
        padymax = size;
      }
    }
  } else if (h === 0) {
    if (w === numW - 1) {
      // h = 0, w = numW-1
      padxmin = 0;
      padymin = padH;
      padxmax = size - padW;
      padymax = size;
    } else if (w === 0) {
      // h = 0, w = 0
      padxmin = padW;
      padymin = padH;
      padxmax = size;
      padymax = size;
    } else {
      // h = 0, w = k
      padxmin = 0;
      padymin = padH;
      padxmax = size;
      padymax = size;
    }
  } else if (h === numH - 1) {
    if (w === numW - 1) {
      // h = numH-1, w = numW-1
      padxmin = 0;
      padymin = 0;
      padxmax = size - padW;
      padymax = size - padH;
    } else if (w === 0) {
      // h = numH-1, w = 0
      padxmin = padW;
      padymin = 0;
      padxmax = size;
      padymax = size - padH;
    } else {
      // h = numH-1, w = k
      padxmin = 0;
      padymin = 0;
      padxmax = size;
      padymax = size - padH;
    }
  } else {
    if (w === 0) {
      // h = k, w = 0
      padxmin = padW;
      padymin = 0;
      padxmax = size;
      padymax = size;
    } else if (w === numW - 1) {
      // h = k, w = numW-1
      padxmin = 0;
      padymin = 0;
      padxmax = size - padW;
      padymax = size;
    } else {
      padxmin = 0;
      padymin = 0;
      padxmax = size;
      padymax = size;
    }
  }
  return [padxmin, padymin, padxmax, padymax];
}

// check whether x, y is in the image not padding
function notInPadding(paddings_list, x, y, bbox_size, ratio) {
  const xleft = x * ratio;
  const ytop = y * ratio;
  const xright = x * ratio;
  const ybottom = y * ratio;

  const [padxmin, padymin, padxmax, padymax] = paddings_list[0];
  return (
    (xleft >= padxmin) &
    (ytop >= padymin) &
    (xright <= padxmax) &
    (ybottom <= padymax)
  );
}

// 标记图像为已完成
function markImageAsCompleted(index) {
  updatCompleteCounter();
  const menuItem = document.getElementById(`menu-item-${index}`);
  if (menuItem) {
    menuItem.classList.add("completed"); // 添加已完成样式
  }
}

function showBlankImage() {
  const container = document.getElementById("image-container");
  container.innerHTML = "";
}

function imageClickHandler(event) {
  const labelSizeInput = document.getElementById("label-size");
  const divSize = parseInt(labelSizeInput.value);

  change = true;
  const ratio = split_size / container_size;
  const rect = this.getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const clickY = event.clientY - rect.top;
  if (
    !notInPadding(paddings[currentImageIndex], clickX, clickY, divSize, ratio)
  ) {
    return;
  }
  const [xcenter, ycenter, width, height] = bboxAdjust(
    clickX,
    clickY,
    divSize,
    ratio,
    paddings[currentImageIndex],
  );
  const divLeft = xcenter - width / 2;
  const divTop = ycenter - height / 2;
  const bboxWidth = width;
  const bboxHeight = height;

  const div = document.createElement("div");
  div.className = "overlay-div";
  div.style.position = "absolute";
  div.style.left = `${divLeft}px`;
  div.style.top = `${divTop}px`;
  div.style.width = `${bboxWidth}px`;
  div.style.height = `${bboxHeight}px`;
  div.style.backgroundColor = classColors[ptype - 1];
  div.style.opacity = "0.5";
  div.dataset.anno_id = anno_ids[currentImageIndex];
  document.getElementById("image-container").appendChild(div);
  annotations[currentImageIndex].push({
    id: ptype - 1,
    x: divLeft,
    y: divTop,
    w: bboxWidth,
    h: bboxHeight,
    anno_id: anno_ids[currentImageIndex],
  });
  labels[currentImageIndex].push({
    id: ptype - 1,
    x: (xcenter * ratio) / split_size,
    y: (ycenter * ratio) / split_size,
    w: (bboxWidth * ratio) / split_size,
    h: (bboxHeight * ratio) / split_size,
    anno_id: anno_ids[currentImageIndex],
  });
  anno_ids[currentImageIndex] += 1;
  updateLabelCounter(currentImageIndex);
  div.addEventListener("click", function () {
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
}

function deleteImage(index) {
  const menuItem = document.getElementById(`menu-item-${index}`);
  if (!menuItem) return;

  // 检查该图像是否已完成标记
  if (menuItem.classList.contains("completed")) {
    const completedIndex = menuItemsCompleted.indexOf(index);
    if (completedIndex !== -1) {
      menuItemsCompleted.splice(completedIndex, 1);
    }
    for (let i = 0; i < menuItemsCompleted.length; i++) {
      if (menuItemsCompleted[i] > index) {
        menuItemsCompleted[i] -= 1;
      }
    }
    // 直接删除图像和菜单项
    completedImageName = completedImageName.filter(
      (name) => name !== imagesName[index],
    );
    images.splice(index, 1);
    imagesName.splice(index, 1);
    detections.splice(index, 1);
    paddings.splice(index, 1);
    updateImageMenu(imagesName);
    labels.splice(index, 1);
    annotations.splice(index, 1);
    anno_ids.splice(index, 1);
    if (images.length === 0) {
      showBlankImage();
      return;
    }
    if (currentImageIndex === index) {
      if (currentImageIndex !== 0) {
        currentImageIndex -= 1;
      }
    } else if (currentImageIndex >= index) {
      currentImageIndex -= 1;
    }
    showImage(currentImageIndex);
  } else {
    const confirmDelete = confirm("該圖像尚未完成標註 確定要進行刪除嗎？");
    for (let i = 0; i < menuItemsCompleted.length; i++) {
      if (menuItemsCompleted[i] > index) {
        menuItemsCompleted[i] -= 1;
      }
    }
    if (confirmDelete) {
      images.splice(index, 1);
      imagesName.splice(index, 1);
      detections.splice(index, 1);
      paddings.splice(index, 1);
      labels.splice(index, 1);
      annotations.splice(index, 1);
      anno_ids.splice(index, 1);
      updateImageMenu(imagesName);
      if (images.length === 0) {
        showBlankImage();
        return;
      }
      if (currentImageIndex === index) {
        if (currentImageIndex !== 0) {
          currentImageIndex -= 1;
        }
      } else if (currentImageIndex >= index) {
        currentImageIndex -= 1;
      }
      showImage(currentImageIndex);
    }
  }
}

function updateImageCounter(index) {
  document.getElementById("image-counter").textContent =
    "圖片數量 " + (index + 1) + " / " + images.length;
}

function updatCompleteCounter() {
  document.getElementById("complete-counter").textContent =
    "完成標註數量 " + completedImageName.length + " / " + images.length;
}

// reset all labels
function labelreset() {
  completedImageName = completedImageName.filter(
    (name) => name !== imagesName[currentImageIndex],
  );
  labels[currentImageIndex] = [];
  const menuItem = document.getElementById(`menu-item-${currentImageIndex}`);
  if (menuItem) {
    menuItem.classList.remove("completed");
  }
  annotations[currentImageIndex] = [];
  anno_ids[currentImageIndex] = 0;
  const imageContainer = document.getElementById("image-container");
  const divs = imageContainer.getElementsByClassName("overlay-div");
  while (divs.length > 0) {
    divs[0].parentNode.removeChild(divs[0]);
  }
  updateLabelCounter(currentImageIndex);
}

function bboxAdjust(x, y, bbox_size, ratio, paddings_list) {
  let [padxmin, padymin, padxmax, padymax] = paddings_list[0];
  padxmin /= ratio;
  padymin /= ratio;
  padxmax /= ratio;
  padymax /= ratio;
  const xleft = x - bbox_size / 2;
  const ytop = y - bbox_size / 2;
  const xright = x + bbox_size / 2;
  const ybottom = y + bbox_size / 2;
  let width = bbox_size;
  let height = bbox_size;
  let xcenter = x;
  let ycenter = y;

  if (xleft < padxmin) {
    width = xright - padxmin;
    xcenter = xright - width / 2;
  } else if (xright > padxmax) {
    width = padxmax - xleft;
    xcenter = xleft + width / 2;
  }

  if (ytop < padymin) {
    height = ybottom - padymin;
    ycenter = ybottom - height / 2;
  } else if (ybottom > padymax) {
    height = padymax - ytop;
    ycenter = ytop + height / 2;
  }

  return [xcenter, ycenter, width, height];
}

function imageMouseOverHandler(event) {
  const labelSizeInput = document.getElementById("label-size");
  const divSize = parseInt(labelSizeInput.value);

  const rect = this.getBoundingClientRect();
  const mouseX = event.clientX - rect.left - divSize / 2;
  const mouseY = event.clientY - rect.top - divSize / 2;

  const overlayDiv = document.createElement("div");
  overlayDiv.className = "overlay-div-preview";
  overlayDiv.style.position = "absolute";
  overlayDiv.style.left = `${mouseX}px`;
  overlayDiv.style.top = `${mouseY}px`;
  overlayDiv.style.width = `${divSize}px`;
  overlayDiv.style.height = `${divSize}px`;
  overlayDiv.style.backgroundColor = classColors[ptype - 1];
  overlayDiv.style.opacity = "0.5";

  overlayDiv.style.pointerEvents = "none";
  document.getElementById("image-container").appendChild(overlayDiv);

  function updateOverlayPosition(event) {
    const newX = event.clientX - rect.left - divSize / 2;
    const newY = event.clientY - rect.top - divSize / 2;
    overlayDiv.style.left = `${newX}px`;
    overlayDiv.style.top = `${newY}px`;
  }

  function removeOverlay() {
    overlayDiv.remove();
    document.removeEventListener("mousemove", updateOverlayPosition);
    document.removeEventListener("mouseout", removeOverlay);
  }

  document.addEventListener("mousemove", updateOverlayPosition);
  document.addEventListener("mouseout", removeOverlay);
}

function imageMouseOutHandler() {
  const overlayDiv = document.querySelector(".overlay-div-preview");
  if (overlayDiv) {
    overlayDiv.remove();
  }
}
