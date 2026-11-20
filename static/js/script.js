// Todas as alterações no servidor são feitas via POST (formulário oculto).
function postTo(url, data) {
    var form = document.createElement("form");
    form.method = "post";
    form.action = url;
    data.next = window.location.pathname + window.location.search;
    Object.keys(data).forEach(function (key) {
        var input = document.createElement("input");
        input.type = "hidden";
        input.name = key;
        input.value = data[key];
        form.appendChild(input);
    });
    document.body.appendChild(form);
    form.submit();
}
function todo() {
    var input = document.querySelector(".inputToDo").value;
    if (input.replace(/\s/g, "") !== "") {
        postTo("/add", {
            todo: input,
            priority: document.querySelector(".addPriority").value,
            due: document.querySelector(".addDue").value,
            category: document.querySelector(".addCategory").value,
        });
    }
}
function editToDo(button) {
    // Usa a linha do botão clicado (antes sempre editava a primeira tarefa).
    var row = button.closest(".notCompletedToDos, .completedToDos");
    var todo = row.querySelector(".todoContent").value;
    var todoID = row.querySelector(".meta").dataset.id;
    if (todo.replace(/\s/g, "") !== "") {
        postTo(`/edit/${todoID}`, { todo: todo });
    }
}
function updateMeta(el) {
    var meta = el.closest(".meta");
    postTo(`/meta/${meta.dataset.id}`, {
        priority: meta.querySelector(".metaPriority").value,
        due: meta.querySelector(".metaDue").value,
        category: meta.querySelector(".metaCategory").value,
    });
}
function addCategory() {
    var name = document.querySelector(".inputCategory").value.trim();
    if (name !== "") {
        postTo("/category/add", { name: name });
    }
}
