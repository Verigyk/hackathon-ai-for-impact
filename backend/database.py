import json
import sqlite3
import time
from contextlib import contextmanager
from .config import APP_DB, SNCF_DB


@contextmanager
def app_db():
    conn = sqlite3.connect(APP_DB, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def sncf_db():
    conn = sqlite3.connect(f'file:{SNCF_DB.as_posix()}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def initialize():
    APP_DB.parent.mkdir(parents=True, exist_ok=True)
    with app_db() as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), owner TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS dossiers(id TEXT PRIMARY KEY, owner TEXT NOT NULL, proposal_id TEXT NOT NULL REFERENCES proposals(id), status TEXT NOT NULL, idempotency_key TEXT NOT NULL, expires_at REAL NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL, UNIQUE(owner,idempotency_key));
        CREATE TABLE IF NOT EXISTS school_allocations(id INTEGER PRIMARY KEY, dossier_id TEXT NOT NULL REFERENCES dossiers(id), train_number TEXT NOT NULL, service_date TEXT NOT NULL, people INTEGER NOT NULL CHECK(people>0), UNIQUE(dossier_id,train_number,service_date));
        CREATE INDEX IF NOT EXISTS allocation_lookup ON school_allocations(train_number,service_date);
        CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY,payload TEXT NOT NULL,created_at REAL NOT NULL);
        ''')
    if not SNCF_DB.exists():
        raise RuntimeError('Base SNCF absente. Exécuter scripts/import_data.py.')
    # Reference schedules are prepared once at startup, outside user requests.
    conn = sqlite3.connect(SNCF_DB)
    conn.execute('CREATE TABLE IF NOT EXISTS reference_services(train_number TEXT,weekday INTEGER,source_date TEXT,PRIMARY KEY(train_number,weekday))')
    if not conn.execute('SELECT 1 FROM reference_services LIMIT 1').fetchone():
        conn.execute('''INSERT INTO reference_services
          SELECT train_number,CAST(strftime('%w',service_date) AS INTEGER),MAX(service_date)
          FROM scheduled_stops GROUP BY train_number,CAST(strftime('%w',service_date) AS INTEGER)''')
        conn.commit()
    conn.close()


def json_value(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def occupied(conn, train, day, now=None):
    now = time.time() if now is None else now
    return conn.execute('''SELECT COALESCE(SUM(a.people),0) FROM school_allocations a
      JOIN dossiers d ON d.id=a.dossier_id WHERE a.train_number=? AND a.service_date=?
      AND (d.status='confirmed' OR (d.status IN ('held','pending') AND d.expires_at>?))''', (train,day,now)).fetchone()[0]
