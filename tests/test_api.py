import tempfile
import unittest
import uuid
import os
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import database
from backend.main import app
from backend.engine import plan
from backend.models import Project
from backend.catalog import PLACES

class ApiTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'data'/'processed'/'test-temp';root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root);self.patch=patch.object(database,'APP_DB',Path(self.temp.name)/'api.sqlite');self.patch.start()
        self.client=TestClient(app);self.client.__enter__();self.headers={'X-Session':str(uuid.uuid4())}
        self.web_patch=patch.dict(os.environ,{'WEB_DISCOVERY':'false'});self.web_patch.start()
    def tearDown(self):
        self.web_patch.stop()
        self.client.__exit__(None,None,None);self.patch.stop();self.temp.cleanup()

    def test_full_pipeline_and_downloadable_snapshot(self):
        payload={'mode':'guided','origin':'Toulouse','date':'2026-11-06','students':28,'companions':2,'theme':'Moyen Âge'}
        result=self.client.post('/api/search',json=payload,headers=self.headers)
        self.assertEqual(result.status_code,200)
        data=result.json();self.assertEqual(len(data['trace']),3);self.assertTrue(data['proposals'])
        option=self.client.post('/api/options',json={'proposal_id':data['proposals'][0]['id'],'idempotency_key':str(uuid.uuid4())},headers=self.headers)
        self.assertEqual(option.status_code,200);self.assertEqual(option.json()['status'],'held')
        pending=self.client.post('/api/prereservations',json={'dossier_id':option.json()['id'],'teacher_name':'Démo','school':'Collège Démo','email':'demo@example.com'},headers=self.headers)
        self.assertEqual(pending.status_code,200);self.assertEqual(pending.json()['status'],'pending')
        rows=self.client.get('/api/dossiers',headers=self.headers).json();self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['payload']['proposal']['id'],data['proposals'][0]['id'])
        self.assertTrue(rows[0]['simulation']);self.assertNotIn('owner',rows[0])

    def test_validation_and_session_boundaries(self):
        self.assertEqual(self.client.post('/api/search',json={'origin':'Toulouse','date':'invalid'},headers=self.headers).status_code,422)
        self.assertEqual(self.client.get('/api/dossiers',headers={'X-Session':'invalid'}).status_code,401)
        self.assertEqual(self.client.post('/api/search',json={'origin':'Commune inconnue','date':'2026-11-06'},headers=self.headers).status_code,422)
        self.assertEqual(self.client.post('/api/prereservations',json={'dossier_id':'missing','teacher_name':'Démo','school':'Démo','email':'not-an-email'},headers=self.headers).status_code,422)

    def test_live_mode_without_inventory_cannot_propose_or_hold(self):
        with patch('backend.engine.DEMO_MODE',False):
            self.assertEqual(plan(Project(origin='Toulouse',date='2026-11-06'),PLACES)['proposals'],[])
        with patch('backend.bookings.DEMO_MODE',False):
            response=self.client.post('/api/options',json={'proposal_id':'missing','idempotency_key':'stable-key'},headers=self.headers)
            self.assertEqual(response.status_code,503)

if __name__=='__main__':unittest.main()
