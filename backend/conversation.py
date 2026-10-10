"""Flexible French input; transport facts remain the engine's responsibility."""
import re
import unicodedata
from datetime import date, timedelta

ALLOWED = {'origin', 'origin_station', 'destination_id', 'destination_station', 'theme', 'level', 'students', 'companions', 'group_total', 'date', 'trip_type', 'earliest', 'latest', 'visit_minutes', 'origin_access_minutes'}
REQUIRED = {'origin': 'votre lieu de départ', 'theme': 'le thème', 'date': 'la date de sortie', 'earliest': 'l’heure de départ', 'latest': 'l’heure limite de retour ou d’arrivée'}
MONTHS = {'janvier':1,'janv':1,'fevrier':2,'fevr':2,'mars':3,'avril':4,'avr':4,'mai':5,'juin':6,'juillet':7,'juil':7,'aout':8,'septembre':9,'sept':9,'octobre':10,'oct':10,'novembre':11,'nov':11,'decembre':12,'dec':12}
CITIES = ('Toulouse','Foix','Carcassonne','Albi','Nîmes','Montpellier','Montauban','Narbonne','Sète','Béziers')

def clean(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(c))

def demo_extract(message, existing):
    text = clean(message)
    fields = {k:v for k,v in existing.items() if k in ALLOWED}
    parsed_date = None
    iso = re.search(r'\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b', text)
    french = re.search(r'\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}|\d{2})\b', text)
    written = re.search(r'\b(\d{1,2}|premier|1er)\s+('+ '|'.join(MONTHS) +r')\.?\s+(\d{4})\b', text)
    try:
        if iso: parsed_date = date(*map(int, iso.groups()))
        elif french: parsed_date = date(int(french[3])+(2000 if len(french[3])==2 else 0),int(french[2]),int(french[1]))
        elif written: parsed_date = date(int(written[3]),MONTHS[written[2]],1 if written[1] in ('premier','1er') else int(written[1]))
        elif 'apres-demain' in text or 'apres demain' in text: parsed_date = date.today()+timedelta(days=2)
        elif re.search(r'\bdemain\b', text): parsed_date = date.today()+timedelta(days=1)
        elif "aujourd'hui" in text or 'aujourd’hui' in text: parsed_date = date.today()
    except ValueError:
        pass
    if parsed_date: fields['date'] = parsed_date.isoformat()
    for key, pattern in [('students',r'(\d+)\s*(?:eleves|enfants)'),('companions',r'(\d+)\s*(?:accompagnat(?:eurs?|rices?)|profs?|enseignants?|adultes)'),('group_total',r'(\d+)\s*(?:personnes|voyageurs|participants)\b'),('visit_minutes',r'(\d+)\s*(?:minutes|min)\s*(?:de\s*)?(?:visite|activite)'),('origin_access_minutes',r'(\d+)\s*(?:minutes|min)\s*(?:jusqu.a|vers|pour)\s*(?:la\s*)?gare')]:
        match = re.search(pattern,text)
        if match: fields[key] = int(match[1])
    if 'students' in fields and 'companions' in fields and re.search(r'\d+\s*(?:eleves|enfants|accompagnat|profs|enseignants)',text):
        fields.pop('group_total',None)
    if re.fullmatch(r'\s*\d+\s*',text) and not (fields.get('students') and fields.get('companions')):
        if 6 <= int(text) <= 200: fields['group_total']=int(text)
    for theme in ('Moyen Âge','Antiquité','Sciences','Nature','Arts','Histoire','Patrimoine'):
        if clean(theme) in text: fields['theme']=theme; break
    custom = re.search(r'(?:theme|sur le theme de)\s*[:=]\s*(.+?)(?:[.;]|$)',message,re.I)
    if custom: fields['theme']=custom[1].strip()
    match = re.search(r'\b([1-6])\s*(?:eme|e|emes|es)\b',text)
    if match: fields['level']=match[1]+'e'
    cities = [(m.start(), city) for city in CITIES for m in re.finditer(r'\b'+re.escape(clean(city))+r'\b',text)]
    cities.sort()
    if cities:
        # A route has two distinct endpoints; a subsequent arrival must not replace departure.
        for pos,city in cities:
            prefix=text[max(0,pos-35):pos]
            if re.search(r'(?:arrivee|destination|vers)\s*(?:a|:)?\s*$',prefix) or (len(cities)>1 and pos==cities[-1][0]):
                fields['destination_station']=city
            else: fields['origin']=city
    if re.search(r'\b(?:aller|allez|alle)\s*[- ]?\s*(?:et\s+)?retour\b|\ba\s*/\s*r\b|\bar\b',text): fields['trip_type']='round_trip'
    elif re.search(r'\b(?:aller|allez|alle)\s+simple\b',text): fields['trip_type']='one_way'
    elif re.search(r'\bretour\b',text): fields['trip_type']='round_trip'
    hours = list(re.finditer(r'\b(\d{1,2})\s*(?:h(?:eures?)?|:)\s*(\d{2})?\b(?:\s*(?:du|de l[’\x27])?\s*(matin|soir|apres[- ]midi))?',text))
    for index,match in enumerate(hours):
        hour=int(match[1]); minute=int(match[2] or 0)
        if match[3] and match[3]!='matin' and hour<12: hour+=12
        if hour>23 or minute>59: continue
        prefix=text[max(0,match.start()-40):match.start()]
        # Inspect only the latest clause, so “aller retour, 9h” is a departure.
        prefix=re.split(r'[,.;]',prefix)[-1]
        prefix=re.sub(r'(?:aller|allez|alle)\s*[- ]?\s*(?:et\s+)?retour','',prefix)
        cues=list(re.finditer(r'avant|retour|arrivee|fin|jusqu|depart|des|apres|partir',prefix))
        key='latest' if (cues and cues[-1][0] in ('avant','retour','arrivee','fin','jusqu')) or (len(hours)>1 and index>0) else 'earliest'
        fields[key]=f'{hour:02d}:{minute:02d}'
    if 'earliest' not in fields and re.search(r'\b(?:depart|partir).*?\bmatin\b',text): fields['earliest']='08:00'
    return fields

def response(fields):
    missing=[label for key,label in REQUIRED.items() if not fields.get(key)]
    if not fields.get('group_total') and not (fields.get('students') and fields.get('companions')):
        missing.append('l’effectif total, élèves et accompagnateurs compris')
    # Duration, school level and approach time are adjustable defaults, never blockers.
    values=dict(fields)
    values.setdefault('trip_type','round_trip')
    values.setdefault('visit_minutes',120)
    values.setdefault('origin_access_minutes',15)
    if missing:
        reply='Bien reçu. Il me manque seulement '+ ' et '.join(missing[:2])+'.'
        if 'la date de sortie' in missing: reply+=' Vous pouvez écrire « 14 septembre 2026 » ou « 14/09/2026 ».'
    else:
        total=fields.get('group_total') or fields['students']+fields['companions']
        button='Vérifier mon trajet' if fields.get('destination_id') or fields.get('destination_station') else 'Découvrir les sorties possibles'
        reply=f"Votre projet est prêt : départ de {fields['origin']}, le {fields['date']}, {total} personnes, {fields['earliest']}–{fields['latest']}, thème {fields['theme']}. Cliquez sur « {button} » pour rechercher les trains compatibles."
    return values,missing,reply
