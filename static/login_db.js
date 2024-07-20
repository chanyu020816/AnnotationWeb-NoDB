let ptype = 1;
let classSet = 1; // 1: 1904, 2: 1921
let mode = "annotate";

function submitForm(event) {
  event.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  fetch("/website/validate_password", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: username,
      password: password,
    }),
  })
    .then((response) => {
      if (response.ok) {
        const formContainer = document.getElementById("form_container");
        const content = document.querySelector(".content");
        const nav = document.querySelector("nav");

        if (formContainer) formContainer.style.display = "none";
        if (content) content.style.display = "block";
        if (nav) nav.style.display = "block";
        const login_set = document.getElementById("login-set").value;
        const page = login_set.split("_")[0];
        const year = login_set.split("_")[1];
        const layer = `Taiwan_${year}`;
        const login_mode = document.getElementById("login-mode").value;
        const url = `/website/${page}_page`;
        window.location.href = url;

        localStorage.setItem("username", username);
        localStorage.setItem("isLogin", true);
        localStorage.setItem("page", page);
        localStorage.setItem("year", year);
        localStorage.setItem("layer", layer);
        localStorage.setItem("login_setting", `${login_set}_${login_mode}`);
      } else {
        const loginStatus = document.getElementById("login-status");
        loginStatus.textContent = "Password Incorrect";
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}
