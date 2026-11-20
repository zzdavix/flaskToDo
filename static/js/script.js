// Alterações no servidor são feitas via POST (formulário oculto).
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

function rowOf(element) {
    return element.closest(".notCompletedToDos, .completedToDos");
}

// Mostra o botão "salvar" assim que o texto da tarefa é alterado.
function markDirty(input) {
    rowOf(input).classList.add("dirty");
}

function editToDo(element) {
    var row = rowOf(element);
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

// Atalho: "/" foca o campo de busca (fora de campos de formulário).
document.addEventListener("keydown", function (event) {
    var tag = (event.target.tagName || "").toLowerCase();
    if (event.key === "/" && tag !== "input" && tag !== "select" && tag !== "textarea") {
        event.preventDefault();
        document.querySelector(".searchBox").focus();
    }
});
