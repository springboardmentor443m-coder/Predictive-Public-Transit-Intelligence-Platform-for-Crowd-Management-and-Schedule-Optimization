from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from app.config import STATIC
from app import services as s
@asynccontextmanager
async def lifespan(app): s.ensure(); yield
app=FastAPI(title='MetroFlow Pro',version='2.0',description='Synthetic-data metro operations prototype',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=str(STATIC)),name='static')
class Scenario(BaseModel): scenario:str=Field(pattern='^(normal|rush_hour|demand_surge|service_disruption)$')
@app.get('/')
def root(): return {'app':'MetroFlow Pro','dashboard':'/dashboard','docs':'/docs'}
@app.get('/dashboard',response_class=HTMLResponse)
def dashboard(): return (STATIC/'dashboard.html').read_text(encoding='utf-8')
@app.get('/health')
def health(): return {'status':'ok','data_mode':'synthetic demo'}
@app.get('/api/overview')
def overview(): return s.overview()
@app.get('/api/stations')
def get_stations(): return s.stations()
@app.get('/api/trains')
def get_trains(): return s.trains()
@app.get('/api/alerts')
def get_alerts(): return s.get_alerts()
@app.get('/api/forecast/{sid}')
def get_forecast(sid:str,horizon_hours:int=6):
 if not 1<=horizon_hours<=24: raise HTTPException(400,'horizon_hours must be 1..24')
 try: return {'station_id':sid,'forecast':s.forecast(sid,horizon_hours)}
 except ValueError: raise HTTPException(404,'Unknown station')
@app.post('/api/simulation/start')
def start(): s.RUNNING=True; return {'running':True}
@app.post('/api/simulation/stop')
def stop(): s.RUNNING=False; return {'running':False}
@app.post('/api/simulation/tick')
def tick(body:Scenario|None=None): return s.tick(body.scenario if body else None)
@app.post('/api/simulation/scenario')
def scenario(body:Scenario): s.SCENARIO=body.scenario; return {'scenario':s.SCENARIO}
@app.post('/api/alerts/{alert_id}/ack')
def ack(alert_id:int):
 c=s.conn(); cur=c.execute('UPDATE alerts SET ack=1 WHERE id=?',(alert_id,)); c.commit(); n=cur.rowcount; c.close()
 if not n: raise HTTPException(404,'Alert not found')
 return {'ok':True}
@app.post('/api/ai/train')
def train(): return s.train_models()
