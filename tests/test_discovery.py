import unittest
from unittest.mock import AsyncMock,patch
from backend.discovery import distance, discover, search_web, station_geography
from backend.models import Project

class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    def test_distance_is_geographic_not_a_walk_estimate(self):
        a={'lat':43.6,'lon':1.4};b={'lat':43.61,'lon':1.4}
        self.assertAlmostEqual(distance(a,a),0)
        self.assertTrue(1100<distance(a,b)<1120)

    async def test_web_search_rejects_lists_and_missing_geography(self):
        data={'query':{'pages':{'1':{'pageid':1,'title':'Château de Foix','coordinates':[{'lat':42.9,'lon':1.6}]},
            '2':{'pageid':2,'title':'Liste des châteaux','coordinates':[{'lat':43,'lon':1}]},
            '3':{'pageid':3,'title':'Musée sans coordonnées'},'4':{'pageid':4,'title':'Occitanie','coordinates':[{'lat':43,'lon':1}]}}}}
        with patch('backend.discovery.cached',return_value=None),patch('backend.discovery.store_cache'),patch('backend.discovery.fetch',new=AsyncMock(return_value=data)):
            result=await search_web(None,'Moyen Âge')
        self.assertEqual([r['pageid'] for r in result],[1])

    async def test_unverified_or_long_walk_never_becomes_a_destination(self):
        station={'code':'test-station','name':'Albi Ville','lat':43.922,'lon':2.138}
        page={'pageid':1,'title':'Cathédrale d’Albi','coordinates':[{'lat':43.928,'lon':2.143}],'extract':'Lieu historique','fullurl':'https://fr.wikipedia.org/wiki/Cathédrale_Sainte-Cécile_d’Albi'}
        with patch('backend.discovery.resolve_station',return_value={'code':'origin'}),patch('backend.discovery.reachable_codes',return_value={'test-station'}),patch('backend.discovery.station_geography',new=AsyncMock(return_value=[station])),patch('backend.discovery.search_web',new=AsyncMock(return_value=[page])),patch('backend.discovery.walking_route',new=AsyncMock(return_value={'individual_minutes':17})),patch('backend.discovery.store_cache'):
            candidates,_,_,rejections=await discover(Project(origin='Toulouse',date='2026-11-06'))
        self.assertEqual(candidates,[])  # ceil(17*1.25)=22: exceeds the school-group target
        self.assertIn('20 min',rejections[0]['reason'])

    async def test_new_web_destination_keeps_sources_and_unknown_openings(self):
        station={'code':'test-station','name':'Moissac','lat':44.1,'lon':1.1}
        page={'pageid':77,'title':'Abbaye Saint-Pierre','coordinates':[{'lat':44.101,'lon':1.101}],'extract':'Une abbaye historique.','fullurl':'https://fr.wikipedia.org/wiki/Abbaye_Saint-Pierre'}
        route={'individual_minutes':10,'distance_m':700,'source':'https://data.geopf.fr/navigation/itineraire','checked_at':'2026-10-10T12:00:00Z'}
        with patch('backend.discovery.resolve_station',return_value={'code':'origin'}),patch('backend.discovery.reachable_codes',return_value={'test-station'}),patch('backend.discovery.station_geography',new=AsyncMock(return_value=[station])),patch('backend.discovery.search_web',new=AsyncMock(return_value=[page])),patch('backend.discovery.walking_route',new=AsyncMock(return_value=route)),patch('backend.discovery.store_cache'):
            candidates,sources,warnings,_=await discover(Project(origin='Toulouse',date='2026-11-06'))
        self.assertEqual(candidates[0]['id'],'web-77')
        self.assertTrue(candidates[0]['access_verified'])
        self.assertFalse(candidates[0]['opening_verified'])
        self.assertEqual(sources[0]['url'],page['fullurl'])
        self.assertIn('ne sont pas vérifiés',warnings[0])
