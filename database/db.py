"""Opens SQLite connections. The pipeline writes; the API only reads."""
import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).parent / "schema.sql"
INDEX_FILE = Path(__file__).parent / "indexes.sql"


def connect(db_path, read_only=False):
    db_path = Path(db_path)
    if read_only:
        if not db_path.exists():
            raise FileNotFoundError(
                f"Database {db_path} not found. Run `python -m pipeline.run_pipeline` first."
            )
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True,
                               check_same_thread=False)
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row          # rows can be read like dictionaries
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn):
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def create_indexes(conn):
    conn.executescript(INDEX_FILE.read_text(encoding="utf-8"))
