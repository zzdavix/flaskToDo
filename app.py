import socket
import sqlite3
import secrets
import dbChecker
from datetime import datetime
from flask import Flask, render_template, redirect, request

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)


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


def validCategory(cursor, value):
    """Devolve o id se a categoria existir; senão None (sem categoria)."""
    try:
        categoryId = int(value)
    except (TypeError, ValueError):
        return None
    found = cursor.execute(
        "select id from categories where id = ?", (categoryId,)
    ).fetchone()
    return found[0] if found else None


@app.route("/")
def index():
    sortBy = request.args.get("sort", "created")
    priorityFilter = request.args.get("priority", "all")
    categoryFilter = request.args.get("category", "all")  # all | none | <id>
    query = request.args.get("q", "").strip()

    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    cursor.execute(
        "select id,todo,date,time,status,editDate,editTime,priority,dueDate,categoryId from todos"
    )
    rows = cursor.fetchall()
    categories = cursor.execute("select id,name from categories order by name").fetchall()
    connection.close()
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


@app.route("/add/<todo>")
def add(todo):
    priority = validPriority(request.args.get("priority"))
    dueDate = validDueDate(request.args.get("due"))
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    categoryId = validCategory(cursor, request.args.get("category"))
    cursor.execute(
        "insert into todos(todo,date,time,priority,dueDate,categoryId) values(?,?,?,?,?,?)",
        (todo, currentDate(), currentTime(), priority, dueDate, categoryId),
    )
    connection.commit()
    connection.close()
    return redirect("/")


@app.route("/meta/<int:id>")
def meta(id):
    priority = validPriority(request.args.get("priority"))
    dueDate = validDueDate(request.args.get("due"))
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    categoryId = validCategory(cursor, request.args.get("category"))
    cursor.execute(
        "update todos set priority = ?, dueDate = ?, categoryId = ? where id = ?",
        (priority, dueDate, categoryId, id),
    )
    connection.commit()
    connection.close()
    return redirect(safeNext(request.args.get("next")))


@app.route("/category/add/<name>")
def categoryAdd(name):
    name = name.strip()[:30]
    if name:
        connection = sqlite3.connect("todos.db")
        # nome único sem diferenciar maiúsculas (COLLATE NOCASE na tabela)
        connection.execute("insert or ignore into categories(name) values(?)", (name,))
        connection.commit()
        connection.close()
    return redirect(safeNext(request.args.get("next")))


@app.route("/category/delete/<int:id>")
def categoryDelete(id):
    connection = sqlite3.connect("todos.db")
    connection.execute("update todos set categoryId = NULL where categoryId = ?", (id,))
    connection.execute("delete from categories where id = ?", (id,))
    connection.commit()
    connection.close()
    return redirect("/")


@app.route("/check/<int:id>")
def check(id):
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    cursor.execute(f'update todos set status = "True" where id = {id}')
    cursor.execute(f'update todos set editDate = "{currentDate()}" where id = {id}')
    cursor.execute(f'update todos set editTime = "{currentTime()}" where id = {id}')
    connection.commit()
    return redirect("/")


@app.route("/uncheck/<int:id>")
def uncheck(id):
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    cursor.execute(f'update todos set status = "False" where id = {id}')
    connection.commit()
    return redirect("/")


@app.route("/edit/<int:id>/<todo>")
def edit(id, todo):
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    cursor.execute(f'update todos set todo = "{todo}" where id = {id}')
    connection.commit()
    return redirect("/")


@app.route("/delete/<int:id>")
def delete(id):
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    cursor.execute(f"delete from todos where id = {id}")
    cursor.execute(f"update sqlite_sequence set seq = seq-1")
    connection.commit()
    return redirect("/")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(
        debug=True,
        host=socket.gethostbyname(socket.gethostname()),
    )
