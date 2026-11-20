import sqlite3
from contextlib import closing
from os.path import exists


def initDb(path="todos.db"):
    """Cria o banco/tabelas se necessário e aplica as migrações (idempotente)."""
    if not exists(path):
        open(path, "x").close()

    with closing(sqlite3.connect(path)) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS "todos" (
            "id"	INTEGER,
            "todo"	TEXT,
            "date"	TEXT,
            "time"	TEXT,
            "status"	TEXT DEFAULT 'False',
            "editDate"	TEXT,
            "editTime"	INTEGER,
            PRIMARY KEY("id" AUTOINCREMENT)
            )"""
        )

        # Migração (Atividade A): prioridade e data de vencimento.
        columns = [row[1] for row in cursor.execute("PRAGMA table_info(todos)")]
        if "priority" not in columns:
            cursor.execute("ALTER TABLE todos ADD COLUMN priority TEXT DEFAULT 'media'")
        if "dueDate" not in columns:
            cursor.execute("ALTER TABLE todos ADD COLUMN dueDate TEXT")

        # Migração (Atividade B): categorias.
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE
            )"""
        )
        if "categoryId" not in columns:
            cursor.execute("ALTER TABLE todos ADD COLUMN categoryId INTEGER")

        connection.commit()
