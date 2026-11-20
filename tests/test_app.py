import re
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta

import pytest

import app as appModule
import dbChecker


def add(client, todo="tarefa", **extra):
    return client.post("/add", data={"todo": todo, **extra})


def titles(client, url="/"):
    html = client.get(url).get_data(as_text=True)
    return re.findall(r'value="([^"]*)" class="todoContent"', html)


# ---------- POST em vez de GET ----------
@pytest.mark.parametrize(
    "url",
    ["/add", "/check/1", "/uncheck/1", "/edit/1", "/delete/1", "/meta/1",
     "/category/add", "/category/delete/1"],
)
def test_mutating_routes_reject_get(client, url):
    assert client.get(url).status_code == 405


def test_old_get_urls_do_not_create_todos(client, db):
    assert client.get("/add/hack").status_code in (404, 405)
    assert db("select count(*) from todos") == [(0,)]


def test_index_get_still_works(client):
    assert client.get("/").status_code == 200


# ---------- CRUD básico ----------
def test_add_check_uncheck_edit_delete(client, db):
    add(client, "comprar pão")
    assert db("select todo,status from todos") == [("comprar pão", "False")]

    client.post("/check/1")
    row = db("select status,editDate,editTime from todos")[0]
    assert row[0] == "True" and row[1] and row[2]

    client.post("/uncheck/1")
    assert db("select status from todos") == [("False",)]

    client.post("/edit/1", data={"todo": "comprar leite"})
    assert db("select todo from todos") == [("comprar leite",)]

    client.post("/delete/1")
    assert db("select count(*) from todos") == [(0,)]


def test_empty_or_blank_todo_is_ignored(client, db):
    add(client, "   ")
    add(client, "")
    assert db("select count(*) from todos") == [(0,)]
    add(client, "ok")
    client.post("/edit/1", data={"todo": "  "})
    assert db("select todo from todos") == [("ok",)]


def test_edit_targets_the_right_row(client, db):
    add(client, "a")
    add(client, "b")
    client.post("/edit/2", data={"todo": "b2"})
    assert db("select todo from todos order by id") == [("a",), ("b2",)]


def test_delete_does_not_reuse_ids(client, db):
    add(client, "a")
    add(client, "b")
    client.post("/delete/2")
    add(client, "c")
    assert [r[0] for r in db("select id from todos order by id")] == [1, 3]


# ---------- Injeção de SQL / texto especial ----------
@pytest.mark.parametrize(
    "text",
    ['"; drop table todos; --', "it's", "a/b?c#d", "100%"],
)
def test_special_text_is_stored_literally(client, db, text):
    add(client, text)
    assert db("select todo from todos") == [(text,)]
    client.post("/edit/1", data={"todo": text + "!"})
    assert db("select todo from todos") == [(text + "!",)]


def test_html_is_escaped_in_page(client):
    add(client, "<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in client.get("/").get_data(as_text=True)


def test_category_name_injection(client, db):
    client.post("/category/add", data={"name": "x'); drop table todos; --"})
    assert db("select name from categories") == [("x'); drop table todos; --",)]
    assert db("select count(*) from todos") == [(0,)]


# ---------- Prioridade e vencimento (A) ----------
def test_priority_and_due_validation(client, db):
    add(client, "a", priority="alta", due="2030-01-02")
    add(client, "b", priority="xx", due="lixo")
    assert db("select priority,dueDate from todos order by id") == [
        ("alta", "2030-01-02"),
        ("media", None),
    ]


def test_overdue_marked_only_when_pending_and_past(client):
    past = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    add(client, "velha", due=past)
    add(client, "futura", due=future)
    assert client.get("/").get_data(as_text=True).count('class="overdueTag"') == 1
    client.post("/check/1")
    assert 'class="overdueTag"' not in client.get("/").get_data(as_text=True)


def test_sort_by_priority_and_due(client):
    add(client, "baixa", priority="baixa")
    add(client, "alta", priority="alta", due="2031-01-01")
    add(client, "media", priority="media", due="2030-01-01")
    assert titles(client, "/?sort=priority") == ["alta", "media", "baixa"]
    assert titles(client, "/?sort=due") == ["media", "alta", "baixa"]


def test_filter_by_priority(client):
    add(client, "a", priority="alta")
    add(client, "b", priority="baixa")
    assert titles(client, "/?priority=alta") == ["a"]


def test_meta_updates_existing_todo(client, db):
    add(client, "a")
    client.post("/meta/1", data={"priority": "baixa", "due": "2030-05-05"})
    assert db("select priority,dueDate from todos") == [("baixa", "2030-05-05")]


# ---------- Categorias e busca (B) ----------
def test_categories_unique_case_insensitive_and_blank_ignored(client, db):
    for name in ["Trabalho", "trabalho", "  "]:
        client.post("/category/add", data={"name": name})
    assert db("select name from categories") == [("Trabalho",)]


def test_category_filter_and_unknown_category(client):
    client.post("/category/add", data={"name": "Casa"})
    add(client, "lavar", category="1")
    add(client, "solta", category="99")
    add(client, "outra")
    assert titles(client, "/?category=1") == ["lavar"]
    assert sorted(titles(client, "/?category=none")) == ["outra", "solta"]


def test_delete_category_keeps_todos(client, db):
    client.post("/category/add", data={"name": "Casa"})
    add(client, "lavar", category="1")
    client.post("/category/delete/1")
    assert db("select categoryId from todos") == [(None,)]
    assert db("select count(*) from categories") == [(0,)]


def test_search_case_insensitive_and_combined(client):
    client.post("/category/add", data={"name": "Casa"})
    add(client, "Lavar louça", category="1", priority="alta")
    add(client, "lavar carro")
    assert sorted(titles(client, "/?q=LAVAR")) == ["Lavar louça", "lavar carro"]
    assert titles(client, "/?q=lavar&category=1&priority=alta") == ["Lavar louça"]
    assert titles(client, "/?q=zzz") == []


# ---------- Redirecionamento seguro ----------
@pytest.mark.parametrize(
    "nxt,expected",
    [("/?q=a", "/?q=a"), ("//evil.com", "/"), ("http://evil.com", "/"), ("", "/")],
)
def test_next_redirect_is_local_only(client, nxt, expected):
    resp = client.post("/add", data={"todo": "x", "next": nxt})
    assert resp.status_code == 302
    assert resp.headers["Location"] == expected


# ---------- Conexões fechadas ----------
class Tracked:
    """Envolve a conexão real para registrar se close() foi chamado."""

    instances = []

    def __init__(self, conn, failing=False):
        self.conn, self.closed, self.failing = conn, False, failing
        Tracked.instances.append(self)

    def execute(self, *a, **k):
        if self.failing:
            raise sqlite3.OperationalError("boom")
        return self.conn.execute(*a, **k)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.closed = True
        self.conn.close()


def patchConnect(monkeypatch, failing=False):
    Tracked.instances = []
    real = sqlite3.connect
    monkeypatch.setattr(
        appModule.sqlite3, "connect", lambda *a, **k: Tracked(real(*a, **k), failing)
    )


def test_connections_are_closed(client, monkeypatch):
    patchConnect(monkeypatch)
    add(client, "a")
    client.get("/")
    client.post("/check/1")
    client.post("/category/add", data={"name": "c"})
    client.post("/delete/1")
    assert Tracked.instances and all(c.closed for c in Tracked.instances)


def test_connection_closed_even_on_error(client, monkeypatch):
    patchConnect(monkeypatch, failing=True)
    with pytest.raises(sqlite3.OperationalError):
        client.post("/delete/1")
    assert Tracked.instances and all(c.closed for c in Tracked.instances)


# ---------- Migração de banco antigo ----------
def test_migration_from_original_schema(tmp_path):
    path = str(tmp_path / "old.db")
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            """CREATE TABLE todos (id INTEGER, todo TEXT, date TEXT, time TEXT,
            status TEXT DEFAULT 'False', editDate TEXT, editTime INTEGER,
            PRIMARY KEY(id AUTOINCREMENT))"""
        )
        conn.execute("insert into todos(todo,date,time) values('antiga','01.01.24','10:00')")
        conn.commit()

    dbChecker.initDb(path)
    dbChecker.initDb(path)  # idempotente

    with closing(sqlite3.connect(path)) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(todos)")]
        assert {"priority", "dueDate", "categoryId"} <= set(cols)
        assert conn.execute("select todo,priority from todos").fetchall() == [("antiga", "media")]
        assert conn.execute("select count(*) from categories").fetchall() == [(0,)]
