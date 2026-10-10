"""Find direct round trips in the dated SNCF snapshot, without inventing schedules."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def stations(conn: sqlite3.Connection, term: str) -> list[dict]:
    return [dict(row) for row in conn.execute('SELECT code,name FROM stations WHERE name LIKE ? ORDER BY name', (f'%{term}%',))]


def direct_legs(conn: sqlite3.Connection, service_date: str, origin: str, destination: str) -> list[dict]:
    query = '''
      SELECT o.train_number, o.departure_seconds,
             CASE WHEN d.arrival_seconds < o.departure_seconds
                  THEN d.arrival_seconds+86400 ELSE d.arrival_seconds END AS arrival_seconds,
             o.source_row AS origin_source_row, d.source_row AS destination_source_row
      FROM scheduled_stops o JOIN scheduled_stops d
        ON o.service_date=d.service_date AND o.train_number=d.train_number
      WHERE o.service_date=? AND o.station_code=? AND d.station_code=?
        AND o.stop_order<d.stop_order
        AND o.departure_seconds IS NOT NULL AND d.arrival_seconds IS NOT NULL
        AND NOT EXISTS (
          SELECT 1 FROM scheduled_stops x
          WHERE x.service_date=o.service_date AND x.train_number=o.train_number
          GROUP BY x.stop_order HAVING COUNT(*)>1
        )
      ORDER BY o.departure_seconds,arrival_seconds
    '''
    return [dict(row) for row in conn.execute(query, (service_date, origin, destination))]


def historical_metrics(conn: sqlite3.Connection, train: str, service_date: str) -> dict | None:
    # A monthly aggregate is not an observation available before that month ends.
    cutoff = int(service_date[:4]) * 100 + int(service_date[5:7])
    result = conn.execute('''SELECT year,month,reported_regularity,reported_cancellation_rate,
      planned_circulations,operated_circulations,source_row FROM train_month_metrics
      WHERE train_number=? AND year*100+month < ? ORDER BY year DESC,month DESC LIMIT 1''', (train, cutoff)).fetchone()
    return dict(result) if result else None


def search(conn: sqlite3.Connection, service_date: str, origin: str, destination: str,
           group_size: int, earliest: int = 8*3600, latest: int = 19*3600,
           min_time_at_destination: int = 4*3600, limit: int = 10) -> dict:
    date.fromisoformat(service_date)
    if not 6 <= group_size <= 50:
        return {'status': 'non_faisable', 'reason': 'Effectif hors de la plage 6 à 50 voyageurs définie dans le cadrage.', 'proposals': []}
    if not 0 <= earliest < latest <= 86400 or min_time_at_destination <= 0:
        raise ValueError('Invalid day-trip time constraints')
    if origin == destination:
        raise ValueError('Origin and destination must be different')
    station_codes = {r[0] for r in conn.execute('SELECT code FROM stations WHERE code IN (?,?)', (origin, destination))}
    if origin not in station_codes or destination not in station_codes:
        raise ValueError('Unknown station code')
    covered = conn.execute('SELECT 1 FROM scheduled_stops WHERE service_date=? LIMIT 1', (service_date,)).fetchone()
    if not covered:
        return {'status': 'donnees_absentes', 'reason': 'Aucun horaire fourni pour cette date. Les dates du fichier ne sont pas transposées.', 'proposals': []}
    outbound = direct_legs(conn, service_date, origin, destination)
    inbound = direct_legs(conn, service_date, destination, origin)
    proposals = []
    for outward in outbound:
        if outward['departure_seconds'] < earliest:
            continue
        for homeward in inbound:
            available_time = homeward['departure_seconds'] - outward['arrival_seconds']
            if available_time < min_time_at_destination or homeward['arrival_seconds'] > latest:
                continue
            proposals.append({
                'outbound': {**outward, 'historical_metrics': historical_metrics(conn, outward['train_number'], service_date)},
                'inbound': {**homeward, 'historical_metrics': historical_metrics(conn, homeward['train_number'], service_date)},
                'time_at_destination_seconds': available_time,
                'total_train_time_seconds': outward['arrival_seconds']-outward['departure_seconds']+homeward['arrival_seconds']-homeward['departure_seconds'],
                'status': 'a_confirmer',
                'checks': {'dated_schedule': True, 'direct_trains': True, 'group_size_within_brief': True,
                           'group_authorization': None, 'available_group_capacity': None,
                           'school_to_station': None, 'station_to_site': None, 'activity_hours': None},
            })
    proposals.sort(key=lambda p: (p['total_train_time_seconds'], -p['time_at_destination_seconds']))
    return {'status': 'a_confirmer' if proposals else 'aucune_proposition', 'service_date': service_date,
            'group_size': group_size, 'total_candidates': len(proposals), 'proposals': proposals[:limit],
            'notice': 'Horaires issus du fichier daté fourni. Capacité, autorisation groupes et activité non vérifiées. Aucune réservation.'}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--stations', help='Search for station names')
    parser.add_argument('--date')
    parser.add_argument('--origin')
    parser.add_argument('--destination')
    parser.add_argument('--group-size', type=int, default=46)
    args = parser.parse_args()
    db = ROOT / 'data' / 'processed' / 'sncf.sqlite'
    with sqlite3.connect(f'file:{db.as_posix()}?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        if args.stations:
            result = stations(conn, args.stations)
        elif args.date and args.origin and args.destination:
            result = search(conn, args.date, args.origin, args.destination, args.group_size)
        else:
            parser.error('Provide --stations or --date, --origin and --destination')
        print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
