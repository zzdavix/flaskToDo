function todo() {
    var input = document.querySelector(".inputToDo").value;
    if (input === "" || input.replace(/\s/g, "") === "") {
    } else {
        var priority = document.querySelector(".addPriority").value;
        var due = document.querySelector(".addDue").value;
        window.location.href =
            `/add/${encodeURIComponent(input)}?priority=${priority}&due=${due}`;
    }
}
function editToDo() {
    var todo = document.querySelector(".todoContent").value;
    var todoID = document.querySelector(".todoID").innerHTML;
    if (todo === "" || todo.replace(/\s/g, "") === "") {
    } else {
        window.location.href = `/edit/${todoID}/${todo}`;
    }
}
function updateMeta(el) {
    var meta = el.closest(".meta");
    var priority = meta.querySelector(".metaPriority").value;
    var due = meta.querySelector(".metaDue").value;
    var next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href =
        `/meta/${meta.dataset.id}?priority=${priority}&due=${due}&next=${next}`;
}
