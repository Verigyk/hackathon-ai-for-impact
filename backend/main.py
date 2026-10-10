import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Depends
from .database import initialize, app_db, sncf_db, json_value
from .models import Project, ChatMessage, OptionRequest, PrereservationRequest
from .catalog import PLACES
from .agents import workflow, chat
from .engine import normalized
from .bookings import create_option, prereserve, list_dossiers, release
from .config import DEMO_MODE
from .providers import llm_enabled, llm_name
from .discovery import recent_places


@asynccontextmanager
async def lifespan(app):
    initialize()
    yield


app=FastAPI(title='SNCF — Planificateur de sorties scolaires liO',version='2.0.0',lifespan=lifespan)


def session(x_session: str=Header()):
    try:
        return str(uuid.UUID(x_session))
    except ValueError:
        raise HTTPException(401,'Session invalide.')


@app.get('/api/health')
def health():
    return {'status':'ok','demo':DEMO_MODE}


@app.get('/api/status')
def status():
    with sncf_db() as conn:
        counts={'stations':conn.execute('SELECT COUNT(*) FROM stations').fetchone()[0], 'stops':conn.execute('SELECT COUNT(*) FROM scheduled_stops').fetchone()[0], 'metrics':conn.execute('SELECT COUNT(*) FROM train_month_metrics').fetchone()[0], 'trains':conn.execute('SELECT COUNT(DISTINCT train_number) FROM scheduled_stops').fetchone()[0]}
        sources=[dict(r) for r in conn.execute('SELECT filename,sha256,kind,imported_at FROM sources')]
    return {'demo':DEMO_MODE,'counts':counts,'sources':sources,'providers':{'llm':llm_enabled(),'name':llm_name() if llm_enabled() else None,'web':os.getenv('WEB_DISCOVERY','true').lower()=='true','web_name':'Wikimedia · SNCF Open Data · IGN'},'quota':50,'ttl_minutes':int(os.getenv('OPTION_TTL_MINUTES','30'))}


@app.get('/api/stations')
def stations(q:str=''):
    with sncf_db() as conn:
        rows=[dict(r) for r in conn.execute('SELECT code,name FROM stations ORDER BY name')]
    return [r for r in rows if normalized(q) in normalized(r['name'])]


@app.get('/api/places')
def places():
    return recent_places() if os.getenv('WEB_DISCOVERY','true').lower()=='true' else PLACES


@app.post('/api/chat')
async def conversation(request:ChatMessage,owner:str=Depends(session)):
    return await chat(request)


@app.post('/api/search')
async def search(project:Project,owner:str=Depends(session)):
    try:
        state=await workflow.ainvoke({'project':project})
    except ValueError as error:
        raise HTTPException(422,str(error))
    result=state['result']; project_id=str(uuid.uuid4()); now=time.time()
    with app_db() as conn:
        conn.execute('INSERT INTO projects VALUES (?,?,?,?)',(project_id,owner,json_value(project.model_dump(mode='json')),now))
        for proposal in result['proposals']:
            conn.execute('INSERT INTO proposals VALUES (?,?,?,?,?)',(proposal['id'],project_id,owner,json_value(proposal),now))
        conn.commit()
    return {**result,'project_id':project_id,'project':project.model_dump(mode='json'),'trace':state['trace'],'warnings':state['warnings'],'web_sources':state.get('web_sources',[]),'mode':'demo' if DEMO_MODE else 'live'}


@app.post('/api/options')
def option(request:OptionRequest,owner:str=Depends(session)):
    return create_option(owner,request.proposal_id,request.idempotency_key)


@app.post('/api/prereservations')
def prebooking(request:PrereservationRequest,owner:str=Depends(session)):
    return prereserve(owner,request)


@app.get('/api/dossiers')
def dossiers(owner:str=Depends(session)):
    return list_dossiers(owner)


@app.post('/api/dossiers/{dossier_id}/release')
def release_dossier(dossier_id:str,owner:str=Depends(session)):
    return release(owner,dossier_id)
