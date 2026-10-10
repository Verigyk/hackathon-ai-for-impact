"""School-only quota. Every itinerary allocation is committed in one transaction."""
import json
import time
import uuid
from fastapi import HTTPException
from .database import app_db, occupied, json_value
from .config import TTL_MINUTES, DEMO_MODE


def public_dossier(row):
    value = dict(row)
    value['payload'] = json.loads(value['payload'])
    if value['status'] in ('held', 'pending') and value['expires_at'] <= time.time():
        value['status'] = 'expired'
    value.pop('owner', None)
    value.pop('idempotency_key', None)
    value['reference'] = 'ECH-' + value['id'][:8].upper()
    value['simulation'] = True
    return value


def create_option(owner, proposal_id, idempotency_key):
    if not DEMO_MODE:
        raise HTTPException(503, 'Inventaire SNCF non connecté : aucune réservation réelle disponible.')
    now = time.time()
    with app_db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        existing = conn.execute('SELECT * FROM dossiers WHERE owner=? AND idempotency_key=?', (owner, idempotency_key)).fetchone()
        if existing:
            if existing['proposal_id'] != proposal_id:
                raise HTTPException(409, 'Cette clé a déjà été utilisée pour un autre trajet.')
            return public_dossier(existing)
        row = conn.execute('SELECT * FROM proposals WHERE id=? AND owner=?', (proposal_id, owner)).fetchone()
        if not row:
            raise HTTPException(404, 'Proposition introuvable dans votre session.')
        if now - row['created_at'] > 1800:
            raise HTTPException(409, 'Proposition expirée. Relancez la recherche pour vérifier la jauge.')
        existing = conn.execute("SELECT * FROM dossiers WHERE owner=? AND proposal_id=? AND status IN ('held','pending','confirmed') AND (status='confirmed' OR expires_at>?)", (owner, proposal_id, now)).fetchone()
        if existing:
            return public_dossier(existing)
        proposal = json.loads(row['payload'])
        people = proposal['group_size']
        if not 6 <= people <= 50:
            raise HTTPException(422, 'Un groupe scolaire doit compter entre 6 et 50 personnes.')
        legs = {(leg['train_number'], leg['service_date']) for leg in (proposal['outbound'], proposal['inbound']) if leg}
        for train, day in sorted(legs):
            engaged = occupied(conn, train, day, now)
            if engaged + people > 50:
                raise HTTPException(409, {'message':'Ce train ne peut plus accueillir votre groupe. Relancez la recherche pour obtenir des alternatives.', 'train':train, 'remaining':max(0,50-engaged), 'requested':people})
        dossier_id = str(uuid.uuid4())
        payload = {'proposal':proposal, 'contact':None, 'notice':'Option locale de démonstration. Aucune transmission à la SNCF.'}
        conn.execute('INSERT INTO dossiers VALUES (?,?,?,?,?,?,?,?)', (dossier_id, owner, proposal_id, 'held', idempotency_key, now+TTL_MINUTES*60, json_value(payload), now))
        for train, day in legs:
            conn.execute('INSERT INTO school_allocations(dossier_id,train_number,service_date,people) VALUES (?,?,?,?)', (dossier_id, train, day, people))
        conn.commit()
        return public_dossier(conn.execute('SELECT * FROM dossiers WHERE id=?', (dossier_id,)).fetchone())


def prereserve(owner, request):
    with app_db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM dossiers WHERE id=? AND owner=?', (request.dossier_id, owner)).fetchone()
        if not row:
            raise HTTPException(404, 'Dossier introuvable.')
        if row['status'] not in ('held','pending') or row['expires_at'] <= time.time():
            raise HTTPException(409, 'Cette option est expirée ou libérée. Recherchez un nouveau trajet.')
        payload = json.loads(row['payload'])
        payload['contact'] = request.model_dump(exclude={'dossier_id'})
        payload['notice'] = 'Demande de pré-réservation enregistrée en démonstration — confirmation en attente. Aucun envoi SNCF.'
        conn.execute("UPDATE dossiers SET status='pending',payload=? WHERE id=?", (json_value(payload), row['id']))
        conn.commit()
        return public_dossier(conn.execute('SELECT * FROM dossiers WHERE id=?', (row['id'],)).fetchone())


def list_dossiers(owner):
    with app_db() as conn:
        return [public_dossier(r) for r in conn.execute('SELECT * FROM dossiers WHERE owner=? ORDER BY created_at DESC', (owner,))]


def release(owner, dossier_id):
    with app_db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM dossiers WHERE id=? AND owner=?', (dossier_id, owner)).fetchone()
        if not row:
            raise HTTPException(404, 'Dossier introuvable.')
        if row['status'] == 'confirmed':
            raise HTTPException(409, 'Une confirmation ne peut pas être libérée ici.')
        conn.execute("UPDATE dossiers SET status='released' WHERE id=?", (dossier_id,))
        conn.commit()
        return public_dossier(conn.execute('SELECT * FROM dossiers WHERE id=?', (dossier_id,)).fetchone())
