const hideTextToggle = document.getElementById("hide-text-attrs");

if (hideTextToggle) {
  hideTextToggle.addEventListener("change", () => {
    document.body.classList.toggle("hide-text-attrs", hideTextToggle.checked);
  });
}
