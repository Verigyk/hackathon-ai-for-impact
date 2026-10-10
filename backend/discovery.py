"""Sourced online discovery, official station geography and calculated walking routes.

No model-generated coordinates, transit options or opening hours enter the planner.
Only fixed public API hosts are fetched, never URLs supplied by a model or web page.
"""
import asyncio
import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
import httpx
from .database import app_db, sncf_db, json_value
from .engine import normalized, resolve_station

WIKI='https://fr.wikipedia.org/w/api.php'
STATIONS='https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/gares-de-voyageurs/exports/json'
ROUTING='https://data.geopf.fr/navigation/itineraire'
DEPARTMENTS={'09','11','12','30','31','32','34','46','48','65','66','81','82'}
_lock=asyncio.Lock()
_network_slots=asyncio.Semaphore(2)

def cached(key, age=86400):
    with app_db() as c:
        row=c.execute('SELECT payload,created_at FROM cache WHERE key=?',(key,)).fetchone()
    return json.loads(row['payload']) if row and time.time()-row['created_at']<age else None

def store_cache(key,value):
    with app_db() as c:
        c.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',(key,json_value(value),time.time()));c.commit()

async def fetch(client,url,params=None):
    async with _network_slots:
        for attempt in range(2):
            response=await client.get(url,params=params)
            if response.status_code in (429,502,503,504) and not attempt:
                await asyncio.sleep(0.5);continue
            response.raise_for_status()
            return response.json()

def distance(a,b):
    lat1,lat2=math.radians(a['lat']),math.radians(b['lat'])
    dlat=lat2-lat1;dlon=math.radians(b['lon']-a['lon'])
    term=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(term)))

async def station_geography(client):
    key='web:stations:v1'
    result=cached(key,7*86400)
    if result is not None:return result
    async with _lock:
        result=cached(key,7*86400)
        if result is not None:return result
        rows=await fetch(client,STATIONS,{'select':'nom,codes_uic,codeinsee,position_geographique'})
        by_uic={}
        for row in rows:
            coords=row.get('position_geographique')
            if not coords or str(row.get('codeinsee',''))[:2] not in DEPARTMENTS:continue
            if not (-180<=float(coords['lon'])<=180 and -90<=float(coords['lat'])<=90):continue
            for uic in re.findall(r'\d{8}',str(row.get('codes_uic',''))):
                by_uic[uic]={'lat':float(coords['lat']),'lon':float(coords['lon']),'municipality_code':row.get('codeinsee')}
        with sncf_db() as c:
            stations=[dict(r) for r in c.execute('SELECT code,name FROM stations')]
        result=[]
        for station in stations:
            match=re.search(r'(\d{8})$',station['code'])
            if match and match[1] in by_uic:result.append({**station,**by_uic[match[1]]})
        store_cache(key,result)
        return result

def search_queries(theme):
    text=normalized(theme)
    if 'moyen' in text or 'mediev' in text:return ['château médiéval Occitanie','Moyen Âge musée Occitanie','cathédrale médiévale Occitanie','abbaye Occitanie Moyen Âge']
    if 'antiqu' in text or 'romain' in text:return ['musée romain Occitanie','monument antique Occitanie']
    if 'science' in text or 'espace' in text:return ['musée sciences Occitanie','muséum histoire naturelle Occitanie']
    if 'nature' in text or 'biodivers' in text:return ['jardin botanique Occitanie','muséum Occitanie']
    if 'art' in text:return ['musée art Occitanie','musée peinture Occitanie']
    return [f'{theme[:120]} musée Occitanie',f'{theme[:120]} monument Occitanie']

async def search_web(client,theme):
    key='web:wiki:v3:'+hashlib.sha256(normalized(theme).encode()).hexdigest()
    result=cached(key)
    if result is not None:return result
    responses=await asyncio.gather(*[fetch(client,WIKI,{
        'action':'query','generator':'search','gsrsearch':q,'gsrlimit':15,
        'prop':'coordinates|extracts|info|pageprops','exintro':1,'explaintext':1,
        'exchars':900,'inprop':'url','format':'json','redirects':1,
    }) for q in search_queries(theme)],return_exceptions=True)
    pages={}
    for response in responses:
        if isinstance(response,Exception):continue
        for page in response.get('query',{}).get('pages',{}).values():
            title=normalized(page.get('title',''))
            if not page.get('coordinates') or 'disambiguation' in page.get('pageprops',{}):continue
            if title.startswith(('liste','histoire de','occitanie','region')):continue
            if not any(word in title for word in ('muse','chateau','cathedrale','cite','abbaye','jardin','arenes','aqueduc','pont','basilique','eglise','grotte','site','observatoire','parc','temple','maison carree')):continue
            pages[str(page['pageid'])]=page
    if not pages and all(isinstance(r,Exception) for r in responses):raise RuntimeError('Recherche Wikimedia indisponible.')
    result=list(pages.values());store_cache(key,result)
    return result

async def walking_route(client,station,point):
    key='web:walk:v1:'+station['code']+f":{point['lat']:.5f},{point['lon']:.5f}"
    result=cached(key,7*86400)
    if result is not None:return result
    data=await fetch(client,ROUTING,{'resource':'bdtopo-osrm','start':f"{station['lon']},{station['lat']}",
        'end':f"{point['lon']},{point['lat']}",'profile':'pedestrian','optimization':'fastest',
        'timeUnit':'second','distanceUnit':'meter','geometryFormat':'geojson'})
    seconds=float(data['duration']);meters=float(data['distance'])
    if seconds<0 or meters<0 or meters>10000:raise ValueError('Itinéraire piéton incohérent.')
    # Preserve group multiplier centrally in the engine, not twice in this provider.
    result={'individual_minutes':math.ceil(seconds/60),'distance_m':round(meters),
        'duration_seconds':seconds,'provider':'IGN Géoplateforme','source':ROUTING,
        'resource_version':data.get('resourceVersion'),'checked_at':datetime.now(timezone.utc).isoformat()}
    store_cache(key,result);return result

def reachable_codes(origin,day):
    weekday=(day.weekday()+1)%7
    with sncf_db() as c:
        rows=c.execute('''SELECT DISTINCT d.station_code FROM reference_services r
        JOIN scheduled_stops o ON o.train_number=r.train_number AND o.service_date=r.source_date
        JOIN scheduled_stops d ON d.train_number=r.train_number AND d.service_date=r.source_date
        WHERE r.weekday=? AND o.station_code=? AND o.stop_order<d.stop_order
        AND EXISTS(SELECT 1 FROM train_month_metrics m WHERE m.train_number=r.train_number)''',(weekday,origin)).fetchall()
    return {r[0] for r in rows}

def activity_art(title):
    title=normalized(title)
    return 'castle' if 'chateau' in title or 'cite' in title else 'cathedral' if 'cathedrale' in title or 'abbaye' in title else 'garden' if 'jardin' in title or 'nature' in title else 'arena' if 'arenes' in title or 'romain' in title else 'city'

async def discover(project):
    """Return researched candidates; the transport engine still rejects incompatible days."""
    origin=resolve_station(project.origin,project.origin_station)
    can_reach=reachable_codes(origin['code'],project.date)
    warnings=[];sources=[];rejections=[]
    async with httpx.AsyncClient(timeout=20,trust_env=False,headers={'User-Agent':'SchoolTripPlanner/2.0 (educational travel research)'}) as client:
        stations,pages=await asyncio.gather(station_geography(client),search_web(client,project.theme))
        if not stations:raise RuntimeError('Aucune gare géolocalisée disponible en Occitanie.')
        prepared=[]
        for page in pages:
            coord=page['coordinates'][0];point={'lat':float(coord['lat']),'lon':float(coord['lon'])}
            if not (-180<=point['lon']<=180 and -90<=point['lat']<=90):continue
            closest=sorted(stations,key=lambda s:distance(s,point))[:3]
            # Department-constrained official stations plus a tight radius exclude other regions.
            nearby=[s for s in closest if distance(s,point)<3000 and s['code'] in can_reach]
            if not nearby:
                rejections.append({'city':page['title'],'reason':'Aucune gare desservie directement et suffisamment proche du site.'});continue
            prepared.append((page,point,nearby))
        # Bound cost and latency; this is a searched candidate set, not exhaustive coverage.
        async def attach(item):
            page,point,nearby=item
            for station in nearby:
                try:
                    route=await walking_route(client,station,point)
                except (httpx.HTTPError,ValueError,KeyError):continue
                if math.ceil(route['individual_minutes']*1.25)>20:continue
                source=page.get('fullurl') or 'https://fr.wikipedia.org/?curid='+str(page['pageid'])
                return {'id':'web-'+str(page['pageid']),'city':station['name'],'title':page['title'],'site':page['title'],
                    'station':station['name'],'station_code':station['code'],'themes':[project.theme],
                    'description':page.get('extract','')[:420],
                    'activity':f"Découverte du site autour du thème « {project.theme} » ; accueil pédagogique à confirmer auprès du lieu.",
                    **point,'walk_minutes':route['individual_minutes'],'urban_minutes':None,'open_from':0,'open_to':24,
                    'source':source,'source_label':'Wikipédia · CC BY-SA','art':activity_art(page['title']),'color':'sage',
                    'access_verified':True,'access_evidence':route,'opening_verified':False,
                    'checked_at':datetime.now(timezone.utc).isoformat(),'catalog_origin':'web'}
            rejections.append({'city':page['title'],'reason':'Accès piéton non calculable ou supérieur à 20 min pour le groupe.'})
            return None
        values=await asyncio.gather(*[attach(item) for item in prepared[:12]])
    candidates=[v for v in values if v]
    for place in candidates:sources.append({'title':place['site'],'url':place['source'],'provider':'Wikimedia','checked_at':place['checked_at']})
    warnings.append('Lieux recherchés sur le web ; coordonnées des gares SNCF et accès piétons IGN. Les ouvertures, tarifs et accueils de groupes ne sont pas vérifiés : contactez le site avant de vous engager.')
    for place in candidates:store_cache('web:place:'+place['id'],place)
    return candidates,sources,warnings,rejections

def get_discovered_place(identity):
    return cached('web:place:'+identity,86400)

def recent_places():
    with app_db() as c:
        rows=c.execute("SELECT payload FROM cache WHERE key LIKE 'web:place:%' AND created_at>? ORDER BY created_at DESC LIMIT 40",(time.time()-86400,)).fetchall()
    return [json.loads(r['payload']) for r in rows]
