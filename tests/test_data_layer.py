import sqlite3
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from import_data import number, seconds, SCHEMA
from search_trips import search, direct_legs


class DataLayerTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.execute("INSERT INTO stations VALUES ('A','Départ')")
        self.conn.execute("INSERT INTO stations VALUES ('B','Destination')")
        self.conn.execute("INSERT INTO sources(id,filename,sha256,kind) VALUES ('stops','test','test','test')")
        self.conn.executemany('INSERT INTO scheduled_stops VALUES (?,?,?,?,?,?,?,?)', [
            ('2026-05-05','1',9*3600,9*3600,'A',0,'stops',2),
            ('2026-05-05','1',10*3600,10*3600,'B',1,'stops',3),
            ('2026-05-05','2',16*3600,16*3600,'B',0,'stops',4),
            ('2026-05-05','2',17*3600,17*3600,'A',1,'stops',5),
        ])

    def tearDown(self):
        self.conn.close()

    def test_missing_is_not_zero(self):
        self.assertIsNone(number(''))
        self.assertEqual(number('0'), 0)
        self.assertAlmostEqual(number('63,20%'), 0.632)

    def test_railway_time_after_midnight_preserves_day(self):
        self.assertEqual(seconds('25:14:00'), 25*3600+14*60)
        self.assertIsNone(seconds(None))
        with self.assertRaises(ValueError):
            seconds('12:75:00')

    def test_round_trip_never_claims_available_capacity(self):
        result = search(self.conn,'2026-05-05','A','B',46)
        self.assertEqual(result['total_candidates'],1)
        self.assertEqual(result['status'],'a_confirmer')
        self.assertIsNone(result['proposals'][0]['checks']['available_group_capacity'])

    def test_uncovered_date_is_not_extrapolated(self):
        self.assertEqual(search(self.conn,'2026-10-30','A','B',46)['status'],'donnees_absentes')

    def test_group_limit_and_time_constraint(self):
        self.assertEqual(search(self.conn,'2026-05-05','A','B',51)['status'],'non_faisable')
        self.assertEqual(search(self.conn,'2026-05-05','A','B',46,latest=16*3600)['proposals'],[])

    def test_duplicate_circulation_is_not_silently_combined(self):
        self.conn.execute('INSERT INTO scheduled_stops VALUES (?,?,?,?,?,?,?,?)',
                          ('2026-05-05','1',11*3600,11*3600,'B',1,'stops',6))
        self.assertEqual(direct_legs(self.conn,'2026-05-05','A','B'),[])


if __name__ == '__main__':
    unittest.main()
