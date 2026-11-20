import os
import socket
import sqlite3
import secrets
import dbChecker
from contextlib import contextmanager
from datetime import datetime
from flask import Flask, render_template, redirect, request

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
app.config["DATABASE"] = os.environ.get("FLASKTODO_DB", "todos.db")
dbChecker.initDb(app.config["DATABASE"])


@contextmanager
def getDb():
    """Abre uma conexão, faz commit ao sair sem erro e SEMPRE fecha."""
    connection = sqlite3.connect(app.config["DATABASE"])
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def currentDate():
    return datetime.now().strftime("%d.%m.%y")


def currentTime():
    return datetime.now().strftime("%H:%M")


PRIORITIES = ("alta", "media", "baixa")
PRIORITY_RANK = {"alta": 0, "media": 1, "baixa": 2}


def validPriority(value):
    return value if value in PRIORITIES else "media"


def validDueDate(value):
    """Aceita apenas AAAA-MM-DD válido; qualquer outra coisa vira None."""
    try:
        datetime.strptime(value or "", "%Y-%m-%d")
        return value
    except ValueError:
        return None


def formatDue(value):
    return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y") if value else ""


def safeNext(target):
    """Só aceita caminhos locais (evita open redirect)."""
    if not target or not target.startswith("/") or target.startswith("//"):
        return "/"
    return target


def validCategory(connection, value):
    """Devolve o id se a categoria existir; senão None (sem categoria)."""
    try:
        categoryId = int(value)
    except (TypeError, ValueError):
        return None
    found = connection.execute(
        "select id from categories where id = ?", (categoryId,)
    ).fetchone()
    return found[0] if found else None


@app.route("/")
def index():
    sortBy = request.args.get("sort", "created")
    priorityFilter = request.args.get("priority", "all")
    categoryFilter = request.args.get("category", "all")  # all | none | <id>
    query = request.args.get("q", "").strip()

    with getDb() as connection:
        rows = connection.execute(
            "select id,todo,date,time,status,editDate,editTime,priority,dueDate,categoryId from todos"
        ).fetchall()
        categories = connection.execute(
            "select id,name from categories order by name"
        ).fetchall()
    categoryNames = dict(categories)

    today = datetime.now().strftime("%Y-%m-%d")
    todos = []
    for row in rows:
        priority = validPriority(row[7])
        due = row[8]
        overdue = bool(due) and due < today and row[4] == "False"
        categoryId = row[9] if row[9] in categoryNames else None
        # índices 0-6: colunas originais; 7 prioridade; 8 vencimento (ISO);
        # 9 vencimento formatado; 10 atrasada?; 11 id da categoria; 12 nome da categoria
        todos.append(
            row[:7]
            + (priority, due, formatDue(due), overdue, categoryId, categoryNames.get(categoryId))
        )

    if priorityFilter in PRIORITIES:
        todos = [t for t in todos if t[7] == priorityFilter]

    if categoryFilter == "none":
        todos = [t for t in todos if t[11] is None]
    elif categoryFilter.isdigit():
        todos = [t for t in todos if t[11] == int(categoryFilter)]

    if query:
        needle = query.lower()
        todos = [t for t in todos if needle in (t[1] or "").lower()]

    if sortBy == "priority":
        todos.sort(key=lambda t: (PRIORITY_RANK[t[7]], t[8] is None, t[8] or ""))
    elif sortBy == "due":
        todos.sort(key=lambda t: (t[8] is None, t[8] or "", PRIORITY_RANK[t[7]]))

    return render_template(
        "/index.html",
        todos=todos,
        categories=categories,
        sortBy=sortBy,
        priorityFilter=priorityFilter,
        categoryFilter=categoryFilter,
        query=query,
    )


def cleanText(value):
    return (value or "").strip()


@app.route("/add", methods=["POST"])
def add():
    todo = cleanText(request.form.get("todo"))
    if todo:
        priority = validPriority(request.form.get("priority"))
        dueDate = validDueDate(request.form.get("due"))
        with getDb() as connection:
            categoryId = validCategory(connection, request.form.get("category"))
            connection.execute(
                "insert into todos(todo,date,time,priority,dueDate,categoryId) values(?,?,?,?,?,?)",
                (todo, currentDate(), currentTime(), priority, dueDate, categoryId),
            )
    return redirect(safeNext(request.form.get("next")))


@app.route("/meta/<int:id>", methods=["POST"])
def meta(id):
    priority = validPriority(request.form.get("priority"))
    dueDate = validDueDate(request.form.get("due"))
    with getDb() as connection:
        categoryId = validCategory(connection, request.form.get("category"))
        connection.execute(
            "update todos set priority = ?, dueDate = ?, categoryId = ? where id = ?",
            (priority, dueDate, categoryId, id),
        )
    return redirect(safeNext(request.form.get("next")))


@app.route("/category/add", methods=["POST"])
def categoryAdd():
    name = cleanText(request.form.get("name"))[:30]
    if name:
        with getDb() as connection:
            # nome único sem diferenciar maiúsculas (COLLATE NOCASE na tabela)
            connection.execute("insert or ignore into categories(name) values(?)", (name,))
    return redirect(safeNext(request.form.get("next")))


@app.route("/category/delete/<int:id>", methods=["POST"])
def categoryDelete(id):
    with getDb() as connection:
        connection.execute("update todos set categoryId = NULL where categoryId = ?", (id,))
        connection.execute("delete from categories where id = ?", (id,))
    return redirect(safeNext(request.form.get("next")))


@app.route("/check/<int:id>", methods=["POST"])
def check(id):
    with getDb() as connection:
        connection.execute(
            "update todos set status = 'True', editDate = ?, editTime = ? where id = ?",
            (currentDate(), currentTime(), id),
        )
    return redirect(safeNext(request.form.get("next")))


@app.route("/uncheck/<int:id>", methods=["POST"])
def uncheck(id):
    with getDb() as connection:
        connection.execute("update todos set status = 'False' where id = ?", (id,))
    return redirect(safeNext(request.form.get("next")))


@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    todo = cleanText(request.form.get("todo"))
    if todo:
        with getDb() as connection:
            connection.execute("update todos set todo = ? where id = ?", (todo, id))
    return redirect(safeNext(request.form.get("next")))


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    with getDb() as connection:
        connection.execute("delete from todos where id = ?", (id,))
    return redirect(safeNext(request.form.get("next")))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(
        debug=True,
        host=socket.gethostbyname(socket.gethostname()),
    )
