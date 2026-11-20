import os
import sys
import tempfile

# Define o banco ANTES de importar app (app inicializa o banco ao ser importado),
# para que os testes nunca toquem no todos.db real.
os.environ["FLASKTODO_DB"] = os.path.join(tempfile.mkdtemp(), "import.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from contextlib import closing

import pytest

import app as appModule
import dbChecker


@pytest.fixture
def client(tmp_path):
    """Cliente de teste com banco novo e isolado por teste."""
    path = str(tmp_path / "test.db")
    dbChecker.initDb(path)
    appModule.app.config["DATABASE"] = path
    appModule.app.config["TESTING"] = True
    return appModule.app.test_client()


@pytest.fixture
def db(client):
    def query(sql, params=()):
        with closing(sqlite3.connect(appModule.app.config["DATABASE"])) as conn:
            return conn.execute(sql, params).fetchall()

    return query
