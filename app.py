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


@app.route("/")
def index():
    sortBy = request.args.get("sort", "created")
    priorityFilter = request.args.get("priority", "all")

    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    cursor.execute("select * from todos")
    rows = cursor.fetchall()
    connection.close()

    today = datetime.now().strftime("%Y-%m-%d")
    todos = []
    for row in rows:
        priority = validPriority(row[7])
        due = row[8]
        overdue = bool(due) and due < today and row[4] == "False"
        # índices 0-6: colunas originais; 7 prioridade; 8 vencimento (ISO);
        # 9 vencimento formatado; 10 atrasada?
        todos.append(row[:7] + (priority, due, formatDue(due), overdue))

    if priorityFilter in PRIORITIES:
        todos = [t for t in todos if t[7] == priorityFilter]

    if sortBy == "priority":
        todos.sort(key=lambda t: (PRIORITY_RANK[t[7]], t[8] is None, t[8] or ""))
    elif sortBy == "due":
        todos.sort(key=lambda t: (t[8] is None, t[8] or "", PRIORITY_RANK[t[7]]))

    return render_template(
        "/index.html",
        todos=todos,
        sortBy=sortBy,
        priorityFilter=priorityFilter,
    )


@app.route("/add/<todo>")
def add(todo):
    priority = validPriority(request.args.get("priority"))
    dueDate = validDueDate(request.args.get("due"))
    connection = sqlite3.connect("todos.db")
    cursor = connection.cursor()
    cursor.execute(
        "insert into todos(todo,date,time,priority,dueDate) values(?,?,?,?,?)",
        (todo, currentDate(), currentTime(), priority, dueDate),
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
    cursor.execute(
        "update todos set priority = ?, dueDate = ? where id = ?",
        (priority, dueDate, id),
    )
    connection.commit()
    connection.close()
    target = request.args.get("next") or "/"
    if not target.startswith("/") or target.startswith("//"):
        target = "/"
    return redirect(target)


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
