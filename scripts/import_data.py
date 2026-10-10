"""Import the two supplied SNCF sources to a local, reproducible SQLite database.

Raw sources are preserved. Missing values stay NULL. Historical schedules never
become a forecast or a claim of available seats.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = {'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5,
          'juin': 6, 'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10,
          'novembre': 11, 'décembre': 12}


def number(value: object) -> float | None:
    if value is None or str(value).strip() == '':
        return None
    value = str(value).replace('\u00a0', '').replace(' ', '').strip()
    percent = value.endswith('%')
    result = float(value.rstrip('%').replace(',', '.'))
    return result / 100 if percent else result


def identifier(value: object) -> str:
    if value is None:
        raise ValueError('Missing train identifier')
    value = str(value).strip()
    return value[:-2] if value.endswith('.0') else value


SCHEMA = '''
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT NOT NULL,
  kind TEXT NOT NULL, imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS train_month_metrics (
  year INTEGER NOT NULL, month INTEGER NOT NULL, train_number TEXT NOT NULL,
  axis TEXT, origin_destination TEXT, planned_circulations INTEGER,
  operated_circulations INTEGER, ridership REAL, delays INTEGER,
  reported_regularity REAL, cancellations INTEGER, reported_cancellation_rate REAL,
  reported_load_compliance REAL, incidents INTEGER, impacted_trains INTEGER,
  sales INTEGER, minutes_lost REAL, source_id TEXT NOT NULL REFERENCES sources(id),
  source_row INTEGER NOT NULL, PRIMARY KEY(year, month, train_number)
);
CREATE INDEX IF NOT EXISTS metrics_train_idx ON train_month_metrics(train_number);
CREATE TABLE IF NOT EXISTS stations (
  code TEXT PRIMARY KEY, name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scheduled_stops (
  service_date TEXT NOT NULL, train_number TEXT NOT NULL,
  arrival_seconds INTEGER, departure_seconds INTEGER,
  station_code TEXT NOT NULL REFERENCES stations(code), stop_order INTEGER NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(id), source_row INTEGER PRIMARY KEY
);
'''


def import_metrics(conn: sqlite3.Connection, path: Path) -> dict:
    raw = path.read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    rows = list(csv.DictReader(text.splitlines(), delimiter=';'))
    conn.execute('DELETE FROM train_month_metrics')
    conn.execute('INSERT OR REPLACE INTO sources(id, filename, sha256, kind) VALUES (?, ?, ?, ?)',
                 ('metrics', path.name, hashlib.sha256(raw).hexdigest(), 'historical_monthly_metrics'))
    names = ['Circ Prévues Théorique', 'Circ Prévues réalisé', 'Frequentation',
             'Nombre de retards PFP', 'Taux régularité du train', 'Nombre de suppressions',
             'Taux SUPP', "Taux de respect de l'emport", "Nombre d'incidents générés",
             'Nombre de trains impactés', 'Nombre de ventes', 'Minutes perdues']
    for source_row, row in enumerate(rows, start=2):
        values = [int(row['Année']), MONTHS[row['Mois'].strip().lower()], identifier(row['N° Train']),
                  row['Axe'], row['Origine / Destination']]
        values += [number(row[name]) for name in names]
        values += ['metrics', source_row]
        conn.execute('INSERT INTO train_month_metrics VALUES (' + ','.join(['?'] * len(values)) + ')', values)
    bounds = conn.execute('SELECT MIN(year*100+month), MAX(year*100+month) FROM train_month_metrics').fetchone()
    return {'rows': len(rows), 'trains': len({r['N° Train'] for r in rows}), 'period': bounds}


def seconds(value: object) -> int | None:
    if value is None or str(value).strip() == '':
        return None
    if isinstance(value, datetime):
        value = value.time()
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    if isinstance(value, time):
        return value.hour * 3600 + value.minute * 60 + value.second
    # Railway schedules may use 24:xx or 25:xx for the following civil day.
    parts = str(value).split(':')
    if len(parts) not in (2, 3):
        raise ValueError(f'Invalid railway time: {value!r}')
    hour, minute = int(parts[0]), int(parts[1])
    second = float(parts[2]) if len(parts) == 3 else 0
    if hour < 0 or not 0 <= minute < 60 or not 0 <= second < 60:
        raise ValueError(f'Invalid railway time: {value!r}')
    return hour * 3600 + minute * 60 + int(second)


def import_stops(conn: sqlite3.Connection, path: Path) -> dict:
    import openpyxl
    if not path.exists():
        raise FileNotFoundError(f'Missing required source: {path}')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    conn.execute('DELETE FROM scheduled_stops')
    conn.execute('DELETE FROM stations')
    conn.execute('INSERT OR REPLACE INTO sources(id, filename, sha256, kind) VALUES (?, ?, ?, ?)',
                 ('stops', path.name, digest, 'dated_schedule_snapshot'))
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = wb['Détail desserte']
    iterator = sheet.iter_rows(values_only=True)
    header = next(iterator)
    expected = ('Date', 'Numéro de circulation', "Heure d'arrivée", "Heure de départ", 'Libellé arrêt', 'Code arrêt', 'Ordre desserte')
    if tuple(header) != expected:
        raise ValueError(f'Unexpected schedule columns: {header!r}')
    stations = {}
    batch = []
    count = 0
    for source_row, row in enumerate(iterator, start=2):
        if not any(value is not None for value in row):
            continue
        date, train, arrival, departure, name, code, order = row
        if not date or not code or name is None or order is None:
            raise ValueError(f'Incomplete schedule at source row {source_row}')
        date = date.date().isoformat() if isinstance(date, datetime) else str(date)[:10]
        # Reject invalid dates rather than silently accepting malformed identifiers.
        datetime.strptime(date, '%Y-%m-%d')
        code = str(code)
        name = str(name)
        if code not in stations:
            stations[code] = name
            conn.execute('INSERT INTO stations VALUES (?, ?)', (code, name))
        elif stations[code] != name:
            raise ValueError(f'Conflicting station labels for {code}')
        batch.append((date, identifier(train), seconds(arrival), seconds(departure),
                      code, int(order), 'stops', source_row))
        count += 1
        if len(batch) >= 5000:
            conn.executemany('INSERT INTO scheduled_stops VALUES (?,?,?,?,?,?,?,?)', batch)
            batch.clear()
            if count % 100000 == 0:
                print(json.dumps({'imported_stops': count}), flush=True)
    if batch:
        conn.executemany('INSERT INTO scheduled_stops VALUES (?,?,?,?,?,?,?,?)', batch)
    wb.close()
    conn.executescript('''
      CREATE INDEX IF NOT EXISTS stops_date_station_idx ON scheduled_stops(service_date,station_code);
      CREATE INDEX IF NOT EXISTS stops_date_train_idx ON scheduled_stops(service_date,train_number,stop_order);
      CREATE INDEX IF NOT EXISTS stops_train_idx ON scheduled_stops(train_number);
    ''')
    min_date, max_date = conn.execute('SELECT MIN(service_date), MAX(service_date) FROM scheduled_stops').fetchone()
    train_count = conn.execute('SELECT COUNT(DISTINCT train_number) FROM scheduled_stops').fetchone()[0]
    circulations = conn.execute('SELECT COUNT(*) FROM (SELECT DISTINCT service_date,train_number FROM scheduled_stops)').fetchone()[0]
    matched = conn.execute('SELECT COUNT(*) FROM (SELECT DISTINCT s.train_number FROM scheduled_stops s JOIN train_month_metrics m ON s.train_number=m.train_number)').fetchone()[0]
    duplicates = conn.execute('SELECT COALESCE(SUM(n-1),0) FROM (SELECT COUNT(*) n FROM scheduled_stops GROUP BY service_date,train_number,stop_order HAVING COUNT(*)>1)').fetchone()[0]
    return {'rows': count, 'stations': len(stations), 'trains': train_count,
            'dated_circulations': circulations, 'period': [min_date,max_date],
            'trains_with_historical_metrics': matched, 'duplicate_stop_keys': duplicates}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=ROOT / 'data' / 'processed' / 'sncf.sqlite')
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.database) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.executescript(SCHEMA)
        result = {'metrics': import_metrics(conn, ROOT / 'data' / 'raw' / 'Data_Hackathon.csv')}
        result['stops'] = import_stops(conn, ROOT / 'data' / 'raw' / 'Detail_desserte.xlsx')
        conn.commit()
        result['integrity'] = conn.execute('PRAGMA integrity_check').fetchone()[0]
        result['foreign_key_issues'] = len(conn.execute('PRAGMA foreign_key_check').fetchall())
    (args.database.parent / 'import_report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
