"""Optional network adapters. Keys stay on the Python server; failures are explicit."""
import json
import os
import httpx
from pydantic import BaseModel, Field
from .config import ROOT


class ExtractedNeed(BaseModel):
    fields: dict = Field(default_factory=dict)
    reply: str = Field(default='', max_length=2000)


def llm_enabled():
    return os.getenv('LLM_PROVIDER','').lower() == 'ollama' or bool(os.getenv('LLM_API_KEY'))


def llm_name():
    return 'Ollama · '+os.getenv('OLLAMA_MODEL','mistral:latest') if os.getenv('LLM_PROVIDER','').lower()=='ollama' else os.getenv('LLM_MODEL','gpt-4.1-mini')


async def llm_json(system, payload):
    if os.getenv('LLM_PROVIDER','').lower() == 'ollama':
        base=os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434').rstrip('/')
        properties={k:{'type':'string','minLength':1} for k in ('origin','origin_station','destination_id','destination_station','theme','level')}
        properties.update({k:{'type':'integer','minimum':minimum,'maximum':maximum} for k,minimum,maximum in [('students',1,200),('companions',1,50),('group_total',6,200),('visit_minutes',30,480),('origin_access_minutes',0,180)]})
        properties.update({'date':{'type':'string','pattern':r'^\d{4}-\d{2}-\d{2}$'},'trip_type':{'type':'string','enum':['round_trip','one_way']},'earliest':{'type':'string','pattern':r'^\d{2}:\d{2}$'},'latest':{'type':'string','pattern':r'^\d{2}:\d{2}$'}})
        format_spec={'type':'object','properties':{'fields':{'type':'object','properties':properties,'additionalProperties':False},'reply':{'type':'string','minLength':1}},'required':['fields','reply']} if 'recognized' in payload else 'json'
        async with httpx.AsyncClient(timeout=httpx.Timeout(180,connect=5),trust_env=False) as client:
            response=await client.post(base+'/api/chat',json={
                'model':os.getenv('OLLAMA_MODEL','mistral:latest'),'stream':False,'format':format_spec,
                'keep_alive':'15m','options':{'temperature':0.1,'num_ctx':4096,'num_predict':500},
                'messages':[{'role':'system','content':system+' Réponds uniquement en JSON.'},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]})
            response.raise_for_status()
            content=response.json().get('message',{}).get('content')
            if not content: raise ValueError('Réponse Ollama vide.')
            return json.loads(content)
    key = os.getenv('LLM_API_KEY')
    if not key:
        raise RuntimeError('Clé LLM absente.')
    base = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
    async with httpx.AsyncClient(timeout=35) as client:
        response = await client.post(base+'/chat/completions', headers={'Authorization':'Bearer '+key}, json={
            'model':os.getenv('LLM_MODEL','gpt-4.1-mini'), 'temperature':0.2,
            'response_format':{'type':'json_object'},
            'messages':[{'role':'system','content':system+' Réponds uniquement en JSON.'}, {'role':'user','content':json.dumps(payload,ensure_ascii=False)}]})
        response.raise_for_status()
        content = response.json()['choices'][0]['message'].get('content')
        if not content:
            raise ValueError('Réponse du modèle vide ou refusée.')
        return json.loads(content)


async def search_places(theme):
    """Return source links; unverified web sites never acquire fabricated access times."""
    key = os.getenv('TAVILY_API_KEY')
    if not key:
        return []
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post('https://api.tavily.com/search', headers={'Authorization':'Bearer '+key}, json={'query':f'Occitanie sortie scolaire {theme} site officiel musée patrimoine','max_results':5,'include_answer':False})
        response.raise_for_status()
        return [{'title':str(r.get('title',''))[:300],'url':str(r.get('url',''))[:1000],'content':str(r.get('content',''))[:1500]} for r in response.json().get('results',[])]
