let ptype = 1;
let classSet = 1; // 1: 1904, 2: 1921
let mode = "annotate";

function submitForm(event) {
  event.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const formContainer = document.getElementById("form_container");
  const content = document.querySelector(".content");
  const nav = document.querySelector("nav");

  if (formContainer) formContainer.style.display = "none";
  if (content) content.style.display = "block";
  if (nav) nav.style.display = "block";

  const login_set = document.getElementById("login-set").value;
  const page = login_set.split("_")[0];
  const year = login_set.split("_")[1];
  const login_mode = document.getElementById("login-mode").value;
  const url = `/${page}_page`;
  window.location.href = url;

  localStorage.setItem("username", username);
  localStorage.setItem("isLogin", true);
  localStorage.setItem("page", page);
  localStorage.setItem("year", year);
  localStorage.setItem("login_setting", `${login_set}_${login_mode}`);
}

function get_url_location() {
  const url = window.location.href.split("/");
  return url[url.length - 1];
}
