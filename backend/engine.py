import math
import time
import unicodedata
import uuid
from datetime import date
from .database import app_db, sncf_db, occupied, json_value
from .models import Project
from .config import DEMO_MODE, MIN_CONFIDENCE


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD',value.lower()) if unicodedata.category(c)!='Mn').replace('-',' ').strip()


def resolve_station(term, code=None):
    with sncf_db() as conn:
        rows = [dict(r) for r in conn.execute('SELECT code,name FROM stations ORDER BY name')]
    if code:
        result = next((r for r in rows if r['code']==code),None)
        if not result:
            raise ValueError('Gare inconnue.')
        return result
    wanted = normalized(term)
    exact = [r for r in rows if normalized(r['name'])==wanted]
    matches = exact or [r for r in rows if normalized(r['name']) in wanted or wanted in normalized(r['name'])]
    if not matches:
        raise ValueError('Précisez une commune ou sélectionnez une gare de départ dans la liste.')
    if len(matches)>1:
        ranked = sorted(matches,key=lambda r:len(normalized(r['name'])),reverse=True)
        # A full station name in a school address is unambiguous; bare ambiguous cities need a selection.
        if normalized(ranked[0]['name']) not in wanted:
            raise ValueError('Plusieurs gares correspondent. Sélectionnez votre gare dans la liste.')
        return ranked[0]
    return matches[0]


def clock(seconds):
    return f'{seconds//3600:02d}:{seconds%3600//60:02d}'


def time_seconds(value):
    return value.hour*3600+value.minute*60


def legs(origin,destination,day):
    weekday=(day.weekday()+1)%7
    with sncf_db() as conn:
        rows=conn.execute('''
          SELECT o.train_number,o.departure_seconds,d.arrival_seconds,r.source_date,
                 o.source_row origin_source_row,d.source_row destination_source_row
          FROM reference_services r
          JOIN scheduled_stops o ON o.train_number=r.train_number AND o.service_date=r.source_date
          JOIN scheduled_stops d ON d.train_number=r.train_number AND d.service_date=r.source_date
          WHERE r.weekday=? AND o.station_code=? AND d.station_code=? AND o.stop_order<d.stop_order
          AND o.departure_seconds IS NOT NULL AND d.arrival_seconds IS NOT NULL
          AND EXISTS(SELECT 1 FROM train_month_metrics m WHERE m.train_number=r.train_number)
          ORDER BY o.departure_seconds
        ''',(weekday,origin,destination)).fetchall()
        result=[]
        for row in rows:
            item=dict(row)
            if item['arrival_seconds']<item['departure_seconds']:
                item['arrival_seconds']+=86400
            if item['arrival_seconds']>86400:
                continue  # school-day MVP; no overnight journeys
            metric=conn.execute('''SELECT year,month,reported_regularity,operated_circulations,source_row
                 FROM train_month_metrics WHERE train_number=? ORDER BY year DESC,month DESC LIMIT 1''',(item['train_number'],)).fetchone()
            item['regularity']=metric['reported_regularity'] if metric else None
            item['metrics_period']=f"{metric['year']}-{metric['month']:02d}" if metric else None
            item['metrics_sample']=metric['operated_circulations'] if metric else None
            item['departure']=clock(item['departure_seconds'])
            item['arrival']=clock(item['arrival_seconds'])
            item['duration_minutes']=(item['arrival_seconds']-item['departure_seconds'])//60
            item['service_date']=day.isoformat()
            item['origin']=origin; item['destination']=destination
            item['authorization_source']='Démo : trains présents dans Data_Hackathon, autorisation simulée'
            result.append(item)
        return result


def availability(train,day):
    with app_db() as conn:
        engaged=occupied(conn,train,day)
        groups=conn.execute('''SELECT COUNT(*) FROM school_allocations a JOIN dossiers d ON d.id=a.dossier_id
           WHERE a.train_number=? AND a.service_date=? AND (d.status='confirmed' OR (d.status IN ('held','pending') AND d.expires_at>?))''',(train,day,time.time())).fetchone()[0]
    return {'capacity':50,'occupied':engaged,'remaining':max(0,50-engaged),'groups':groups,'source':'Inventaire scolaire local de démonstration'}


def seed_busy(train,day):
    """Add an anonymous 30-person school group once; actual inventory, never a fake count."""
    identity=f'demo-busy-{day}-{train}'
    with app_db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        existing=conn.execute('SELECT status FROM dossiers WHERE id=?',(identity,)).fetchone()
        if existing and existing['status']!='released':
            conn.rollback(); return
        if occupied(conn,train,day)>20:
            conn.rollback(); return
        if existing:
            conn.execute("UPDATE dossiers SET status='confirmed' WHERE id=?",(identity,))
            conn.commit(); return
        conn.execute('INSERT OR IGNORE INTO projects VALUES (?,?,?,?)',
                     (identity,'demo','{}',time.time()))
        conn.execute('INSERT OR IGNORE INTO proposals VALUES (?,?,?,?,?)',(identity,identity,'demo','{}',time.time()))
        conn.execute('INSERT INTO dossiers VALUES (?,?,?,?,?,?,?,?)',
                     (identity,'demo',identity,'confirmed',identity,0,'{}',time.time(),) )
        conn.execute('INSERT INTO school_allocations(dossier_id,train_number,service_date,people) VALUES (?,?,?,?)',
                     (identity,train,day,30))
        conn.commit()


def confidence(outward,homeward,walk,urban,margin):
    regularities=[leg['regularity'] for leg in (outward,homeward) if leg]
    if any(value is None for value in regularities):
        return {'score':None,'factors':[],'reason':'Régularité historique indisponible.'}
    regularity=min(regularities)
    factors=[
      {'label':'Régularité historique','value':round(regularity*100),'weight':40,'detail':'Minimum des trains utilisés, dernière période disponible'},
      {'label':'Marges de la journée','value':round(min(1,margin/30)*100),'weight':25,'detail':f'{margin} min de marge avant le retour' if homeward else 'Marge d’arrivée et d’activité'},
      {'label':'Accès au site','value':85 if urban else max(60,100-max(0,walk-10)*2),'weight':20,'detail':'Accès urbain simulé' if urban else f'{walk} min à pied pour le groupe (hypothèse)'},
      {'label':'Simplicité du trajet','value':90 if urban else 100,'weight':15,'detail':'Trains directs, accès urbain' if urban else 'Trains directs, accès à pied'},
    ]
    return {'score':round(sum(f['value']*f['weight']/100 for f in factors)),'factors':factors,
            'version':'1.0','notice':'Indice calculé, pas une probabilité. Annulations exclues. Accès simulés.'}


def plan(project:Project,places:list[dict]):
    if not 6 <= project.group_size <= 50:
        return {'proposals':[],'rejections':[{'city':'Effectif scolaire','reason':'La jauge scolaire accepte de 6 à 50 personnes, élèves et accompagnateurs compris.'}],'origin':None}
    if not DEMO_MODE:
        return {'proposals':[],'rejections':[{'city':'Toutes destinations','reason':'Autorisations et inventaire SNCF réels non connectés. Activez le mode démonstration pour tester.'}],'origin':None}
    origin=resolve_station(project.origin,project.origin_station)
    proposals=[]; rejected=[]
    for place in places:
        try:
            destination=resolve_station(place['station'],place.get('station_code'))
        except ValueError as error:
            rejected.append({'city':place['city'],'reason':str(error)}); continue
        if destination['code']==origin['code']:
            rejected.append({'city':place['city'],'reason':'La destination correspond à votre gare de départ.'}); continue
        outward=legs(origin['code'],destination['code'],project.date)
        homeward=legs(destination['code'],origin['code'],project.date) if project.trip_type=='round_trip' else [None]
        walk=math.ceil(place['walk_minutes']*1.25)
        urban=walk>20 and place.get('urban_minutes') is not None
        if place.get('catalog_origin')=='web' and not place.get('access_verified'):
            rejected.append({'city':place['city'],'reason':'Accès au site non vérifié.'});continue
        access=place['urban_minutes'] if urban else walk
        if walk>20 and not urban:
            rejected.append({'city':place['city'],'reason':f'Accès à pied de groupe estimé à {walk} min, sans alternative urbaine configurée.'}); continue
        eligible=[leg for leg in outward if leg['departure_seconds']>=time_seconds(project.earliest)+(project.origin_access_minutes+15)*60]
        if project.scenario=='busy' and eligible:
            seed_busy(eligible[0]['train_number'],project.date.isoformat())
        options=[]; capacity_blocked=False; reliability_blocked=False
        for out in eligible:
            out={**out,'availability':availability(out['train_number'],project.date.isoformat())}
            if out['availability']['remaining']<project.group_size:
                capacity_blocked=True; continue
            visit_start=max(out['arrival_seconds']+(access+15)*60,place['open_from']*3600)
            visit_end=visit_start+project.visit_minutes*60
            if visit_end>place['open_to']*3600:
                continue
            for back in homeward:
                margin=30
                if back:
                    back={**back,'availability':availability(back['train_number'],project.date.isoformat())}
                    if back['availability']['remaining']<project.group_size:
                        capacity_blocked=True; continue
                    earliest_return=visit_end+(access+15+30)*60
                    if back['departure_seconds']<earliest_return:
                        continue
                    if back['arrival_seconds']+project.origin_access_minutes*60>time_seconds(project.latest):
                        continue
                    margin=(back['departure_seconds']-earliest_return)//60
                elif visit_end>time_seconds(project.latest):
                    continue
                score=confidence(out,back,walk,urban,margin)
                if place.get('access_verified'):
                    score['notice']='Indice calculé, pas une probabilité. Annulations exclues. Accès calculé par IGN ; ouverture du lieu à confirmer.'
                    for factor in score.get('factors',[]):
                        if factor['label']=='Accès au site':factor['detail']=f'{walk} min pour le groupe, itinéraire piéton IGN avec marge de 25 %'
                if score['score'] is None or score['score'] < MIN_CONFIDENCE:
                    reliability_blocked=True; continue
                journey=out['duration_minutes']+(back['duration_minutes'] if back else 0)
                options.append({'outbound':out,'inbound':back,'confidence':score,'visit_start':clock(visit_start),
                                'visit_end':clock(visit_end),'visit_start_seconds':visit_start,'margin_minutes':margin,
                                'train_minutes':journey,'access_minutes':access,'access_mode':'urban' if urban else 'walk'})
        if not options:
            reason='Indice de confiance indisponible ou inférieur au seuil de démonstration.' if reliability_blocked else ('Jauge scolaire insuffisante ou aucun autre horaire compatible.' if capacity_blocked else 'Aucun trajet direct compatible avec vos horaires et la durée de visite.')
            rejected.append({'city':place['city'],'reason':reason}); continue
        options.sort(key=lambda v:(-(v['confidence']['score'] or 0),v['train_minutes'],v['outbound']['departure_seconds']))
        best=options[0]
        school_departure=best['outbound']['departure_seconds']-(project.origin_access_minutes+15)*60
        timeline=[{'time':clock(school_departure),'title':'Départ du groupe','detail':f"{project.origin} → gare, {project.origin_access_minutes} min déclarées",'kind':'school'},
                  {'time':best['outbound']['departure'],'title':f"Train liO {best['outbound']['train_number']}",'detail':f"{origin['name']} → {destination['name']}",'kind':'train'},
                  {'time':best['outbound']['arrival'],'title':'Arrivée et accès au site','detail':f"{access} min {'en transport urbain' if urban else 'à pied pour le groupe'} (démo)",'kind':'walk'},
                  {'time':best['visit_start'],'title':place['site'],'detail':place['activity'],'kind':'activity'},
                  {'time':best['visit_end'],'title':'Fin de l’activité','detail':'Pause et préparation du retour' if best['inbound'] else 'Fin du trajet aller simple','kind':'break'}]
        if best['inbound']:
            timeline.extend([{'time':clock(best['visit_start_seconds']+project.visit_minutes*60+30*60),'title':'Temps libre encadré','detail':f"Pause déjeuner de 30 min puis {best['margin_minutes']} min de marge avant le départ vers la gare",'kind':'break'},
                             {'time':clock(best['inbound']['departure_seconds']-(access+15)*60),'title':'Retour à la gare','detail':f"{access} min {'en réseau urbain' if urban else 'à pied'} (démo), puis 15 min de marge d’embarquement",'kind':'walk'},
                             {'time':best['inbound']['departure'],'title':f"Train retour liO {best['inbound']['train_number']}",'detail':f"{destination['name']} → {origin['name']}",'kind':'train'},
                             {'time':best['inbound']['arrival'],'title':'Arrivée à la gare de départ','detail':f"Retour à l’établissement : {project.origin_access_minutes} min déclarées",'kind':'walk'},
                             {'time':clock(best['inbound']['arrival_seconds']+project.origin_access_minutes*60),'title':'Retour du groupe','detail':project.origin,'kind':'school'}])
        proposal={**best,'id':str(uuid.uuid4()),'place':place,'origin':origin,'destination':destination,
                          'group_size':project.group_size,'students':None if project.group_total is not None else project.students,'companions':None if project.group_total is not None else project.companions,
                          'date':project.date.isoformat(),'trip_type':project.trip_type,'timeline':timeline,
                          'status':'compatible_demo','alternative_count':len(options)-1,
                          'transport_estimate_eur':math.ceil(project.group_size/10)*10*(2 if best['inbound'] else 1),
                          'explanation':f"{place['site']} correspond au thème « {project.theme} ». Le trajet est direct, l’effectif de {project.group_size} personnes entre dans la jauge scolaire et les horaires permettent {project.visit_minutes} minutes d’activité.",
                          'assumptions':['Horaires historiques transposés au même jour de semaine','Autorisations scolaires simulées pour les trains du fichier statistique','Accès et ouverture du site : hypothèses de démonstration','Inventaire scolaire local, sans connexion SNCF'],
                          'sources':[{'label':'Horaires SNCF fournis','type':'real','detail':best['outbound']['source_date']},
                                     {'label':'Régularité historique','type':'real','detail':best['outbound']['metrics_period']},
                                     {'label':'Site officiel du lieu','type':'link','url':place.get('source','')},
                                     {'label':'Accès, horaires activité et jauge','type':'demo','detail':'Hypothèses du prototype'}]}
        if place.get('catalog_origin')=='web':
            proposal['assumptions']=['Horaires historiques transposés au même jour de semaine (périmètre du hackathon)',
                'Autorisations et inventaire scolaire simulés ; aucune réservation SNCF réelle',
                'Ouverture et accueil pédagogique non vérifiés : confirmation auprès du lieu nécessaire',
                'Temps de marche IGN majoré de 25 % pour le groupe ; accessibilité PMR non vérifiée']
            proposal['sources'][2]={'label':'Lieu recherché sur le web · Wikipédia CC BY-SA','type':'web','url':place['source']}
            proposal['sources'][3]={'label':'Accès piéton calculé · IGN Géoplateforme','type':'web','url':place['access_evidence']['source'],
                'detail':f"{place['access_evidence']['distance_m']} m · calculé le {place['access_evidence']['checked_at']}"}
            for event in timeline:
                if event['kind']=='walk':event['detail']=event['detail'].replace('(démo)','(calcul IGN + marge groupe)')
        proposals.append(proposal)
    proposals.sort(key=lambda p:-(p['confidence']['score'] or 0))
    return {'proposals':proposals[:6],'rejections':rejected,'origin':origin}
