import sqlite3
from os.path import exists

if exists("todos.db") == False:
    open("todos.db", "x")

connection = sqlite3.connect("todos.db")
cursor = connection.cursor()

try:
    cursor.execute("""SELECT * FROM todos; """).fetchall()
except:
    todosTable = """
    CREATE TABLE "todos" (
	"id"	INTEGER,
    "todo"	TEXT,
    "date"	TEXT,
    "time"	TEXT,
    "status"	TEXT DEFAULT 'False',
    "editDate"	TEXT,
    "editTime"	INTEGER,
    PRIMARY KEY("id" AUTOINCREMENT)
    );"""
    cursor.execute(todosTable)
    connection.commit()

# Migração (Atividade A): adiciona prioridade e data de vencimento em bancos
# existentes. Idempotente: só altera a tabela se as colunas ainda não existirem.
existingColumns = [row[1] for row in cursor.execute("PRAGMA table_info(todos)")]
if "priority" not in existingColumns:
    cursor.execute("ALTER TABLE todos ADD COLUMN priority TEXT DEFAULT 'media'")
if "dueDate" not in existingColumns:
    cursor.execute("ALTER TABLE todos ADD COLUMN dueDate TEXT")

# Migração (Atividade B): tabela de categorias e vínculo opcional na tarefa.
cursor.execute(
    """CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
    )"""
)
if "categoryId" not in existingColumns:
    cursor.execute("ALTER TABLE todos ADD COLUMN categoryId INTEGER")
connection.commit()
connection.close()
