from sqlalchemy import text

from app.db.session import SessionLocal


def test_sqlite_pragmas_configured_for_concurrency():
    db = SessionLocal()
    try:
        busy_timeout = db.execute(text("PRAGMA busy_timeout")).scalar_one()
        journal_mode = db.execute(text("PRAGMA journal_mode")).scalar_one()

        assert busy_timeout >= 30000
        assert str(journal_mode).lower() == "wal"
    finally:
        db.close()
