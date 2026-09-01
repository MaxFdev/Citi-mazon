const addButton = document.getElementById("add-attribute");
const rowsContainer = document.getElementById("attribute-rows");
const rowTemplate = document.getElementById("attribute-row-template");

if (addButton && rowsContainer && rowTemplate) {
  addButton.addEventListener("click", () => {
    const row = rowTemplate.content.firstElementChild.cloneNode(true);
    rowsContainer.appendChild(row);
  });
}
