import pytest
import database.db as db_module
from app import app as flask_app
from database.db import init_db, create_user, get_db


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))
    with flask_app.app_context():
        init_db()
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_user_id(app):
    uid = create_user("Test User", "test@example.com", "password123")
    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?,?,?,?,?)",
        [
            (uid, 100.0, "Food",      "2026-01-03", "Groceries"),
            (uid,  50.0, "Transport", "2026-01-02", "Bus"),
            (uid,  50.0, "Bills",     "2026-01-01", "Electric"),
        ],
    )
    conn.commit()
    conn.close()
    return uid


@pytest.fixture
def zero_user_id(app):
    return create_user("Empty User", "empty@example.com", "password123")
