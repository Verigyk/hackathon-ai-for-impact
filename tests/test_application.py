import json
import sys
import tempfile
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from backend import database
from backend.database import app_db, initialize, json_value, occupied
from backend.bookings import create_option, prereserve, list_dossiers, release
from backend.models import Project, PrereservationRequest, ChatMessage
from backend.engine import plan, confidence, seed_busy
from backend.catalog import PLACES
from backend.agents import demo_extract

TEST_DIR=Path(__file__).resolve().parents[1]/'data'/'processed'/'test-temp'
TEST_DIR.mkdir(parents=True,exist_ok=True)


class BookingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=TEST_DIR); self.patch=patch.object(database,'APP_DB',Path(self.temp.name)/'test.sqlite');self.patch.start();initialize()
        self.owner=str(uuid.uuid4())

    def tearDown(self):
        self.patch.stop();self.temp.cleanup()

    def proposal(self,people=30,owner=None,out='100',back='200',day='2026-11-06'):
        owner=owner or self.owner; pid=str(uuid.uuid4());project_id=str(uuid.uuid4())
        value={'group_size':people,'outbound':{'train_number':out,'service_date':day},'inbound':{'train_number':back,'service_date':day} if back else None}
        with app_db() as c:
            c.execute('INSERT INTO projects VALUES (?,?,?,?)',(project_id,owner,'{}',time.time()))
            c.execute('INSERT INTO proposals VALUES (?,?,?,?,?)',(pid,project_id,owner,json_value(value),time.time()));c.commit()
        return pid

    def test_shared_school_quota_exactly_fifty_then_reject(self):
        first=create_option(self.owner,self.proposal(30),'first-key')
        second=create_option(self.owner,self.proposal(20),'second-key')
        with self.assertRaises(HTTPException) as e:create_option(self.owner,self.proposal(6),'third-key')
        self.assertEqual(e.exception.status_code,409)
        with app_db() as c:self.assertEqual(occupied(c,'100','2026-11-06'),50)

    def test_return_failure_rolls_back_outbound(self):
        create_option(self.owner,self.proposal(45,out='300',back='200'),'occupied-return')
        with self.assertRaises(HTTPException):create_option(self.owner,self.proposal(10,out='100',back='200'),'blocked-return')
        with app_db() as c:self.assertEqual(occupied(c,'100','2026-11-06'),0)

    def test_idempotency_and_prebooking_do_not_double_count(self):
        pid=self.proposal(30);a=create_option(self.owner,pid,'stable-key');b=create_option(self.owner,pid,'stable-key')
        self.assertEqual(a['id'],b['id'])
        d=prereserve(self.owner,PrereservationRequest(dossier_id=a['id'],teacher_name='Prof Test',school='Collège test',email='demo@example.com'))
        self.assertEqual(d['status'],'pending')
        with app_db() as c:self.assertEqual(occupied(c,'100','2026-11-06'),30)

    def test_expired_and_released_options_release_capacity(self):
        d=create_option(self.owner,self.proposal(50),'expire-key')
        with app_db() as c:c.execute('UPDATE dossiers SET expires_at=? WHERE id=?',(time.time()-1,d['id']));c.commit()
        self.assertEqual(list_dossiers(self.owner)[0]['status'],'expired')
        d2=create_option(self.owner,self.proposal(50),'new-option')
        release(self.owner,d2['id'])
        with app_db() as c:self.assertEqual(occupied(c,'100','2026-11-06'),0)

    def test_sessions_cannot_read_or_book_each_others_proposals(self):
        pid=self.proposal();other=str(uuid.uuid4())
        with self.assertRaises(HTTPException) as e:create_option(other,pid,'other-key')
        self.assertEqual(e.exception.status_code,404)
        d=create_option(self.owner,pid,'owner-key');self.assertEqual(list_dossiers(other),[])
        with self.assertRaises(HTTPException):release(other,d['id'])

    def test_concurrent_requests_never_overbook(self):
        requests=[(str(uuid.uuid4()),str(uuid.uuid4())) for _ in range(12)]
        prepared=[(owner,self.proposal(6,owner=owner),key) for owner,key in requests]
        def book(args):
            try:create_option(*args);return True
            except HTTPException as e:self.assertEqual(e.status_code,409);return False
        with ThreadPoolExecutor(max_workers=12) as pool:success=list(pool.map(book,prepared))
        self.assertEqual(sum(success),8)
        with app_db() as c:self.assertEqual(occupied(c,'100','2026-11-06'),48)

    def test_different_dates_have_separate_quotas(self):
        create_option(self.owner,self.proposal(50),'day-one')
        create_option(self.owner,self.proposal(50,day='2026-11-13'),'day-two')
        with app_db() as c:self.assertEqual(occupied(c,'100','2026-11-13'),50)

    def test_busy_fixture_can_be_reactivated_without_duplicate_allocation(self):
        seed_busy('100','2026-11-06')
        with app_db() as c:
            c.execute("UPDATE dossiers SET status='released' WHERE owner='demo'");c.commit()
            self.assertEqual(occupied(c,'100','2026-11-06'),0)
        seed_busy('100','2026-11-06')
        with app_db() as c:
            self.assertEqual(occupied(c,'100','2026-11-06'),30)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM school_allocations').fetchone()[0],1)

    def test_quota_rechecked_after_search(self):
        earlier=self.proposal(25);create_option(self.owner,self.proposal(30),'late-group')
        with self.assertRaises(HTTPException):create_option(self.owner,earlier,'earlier-result')


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(dir=TEST_DIR);cls.patch=patch.object(database,'APP_DB',Path(cls.temp.name)/'test.sqlite');cls.patch.start();initialize()
    @classmethod
    def tearDownClass(cls):cls.patch.stop();cls.temp.cleanup()

    def test_historical_weekday_transposed_and_full_day_coherent(self):
        p=Project(origin='Toulouse',date='2026-11-06')
        r=plan(p,PLACES)
        self.assertGreater(len(r['proposals']),0)
        for proposal in r['proposals']:
            self.assertEqual(proposal['outbound']['service_date'],'2026-11-06')
            from datetime import date
            self.assertEqual(date.fromisoformat(proposal['outbound']['source_date']).weekday(),p.date.weekday())
            self.assertLess(proposal['outbound']['arrival'],proposal['visit_start'])
            self.assertLess(proposal['visit_end'],proposal['inbound']['departure'])
            self.assertGreaterEqual(proposal['outbound']['availability']['remaining'],p.group_size)

    def test_one_way_needs_no_return(self):
        p=Project(origin='Toulouse',date='2026-11-06',trip_type='one_way')
        r=plan(p,PLACES);self.assertTrue(r['proposals'])
        self.assertTrue(all(x['inbound'] is None for x in r['proposals']))

    def test_over_fifty_rejected_before_display(self):
        p=Project(origin='Toulouse',date='2026-11-06',students=49,companions=2)
        self.assertEqual(plan(p,PLACES)['proposals'],[])

    def test_confidence_threshold_filters_before_display(self):
        with patch('backend.engine.MIN_CONFIDENCE',100):
            r=plan(Project(origin='Toulouse',date='2026-11-06'),PLACES)
            self.assertEqual(r['proposals'],[])
            self.assertTrue(any('confiance' in x['reason'] for x in r['rejections']))

    def test_confidence_unknown_stays_unknown_and_no_cancellations(self):
        self.assertIsNone(confidence({'regularity':None},None,10,False,30)['score'])
        a=confidence({'regularity':.9,'cancellations':0},None,10,False,30)
        b=confidence({'regularity':.9,'cancellations':100},None,10,False,30)
        self.assertEqual(a,b);self.assertEqual(sum(f['weight'] for f in a['factors']),100)

    def test_chat_extracts_iso_date_and_does_not_invent_missing_fields(self):
        result=demo_extract('Moyen Âge avec 28 élèves de 5e à Toulouse le 2026-11-06',{})
        self.assertEqual(result['date'],'2026-11-06');self.assertEqual(result['students'],28)
        self.assertNotIn('companions',result);self.assertNotIn('latest',result)


if __name__=='__main__':unittest.main()
