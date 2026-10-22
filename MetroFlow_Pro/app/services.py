import sqlite3, random
from datetime import datetime
import pandas as pd, joblib
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.metrics import mean_absolute_error
from app.config import DATA, DB
from app.data.generate_data import generate
SCENARIO='normal'; RUNNING=False; TICK=0

def ensure():
 if not (DATA/'ridership_hourly.csv').exists(): generate()
def conn():
 c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,created TEXT,type TEXT,severity TEXT,station TEXT,message TEXT,ack INTEGER DEFAULT 0,source TEXT)'); c.commit(); return c
def alert(typ,sev,station,msg,source='simulation'):
 c=conn(); c.execute('INSERT INTO alerts(created,type,severity,station,message,source) VALUES(?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),typ,sev,station,msg,source)); c.commit(); c.close()
def get_alerts():
 c=conn(); rows=c.execute('SELECT id,created,type,severity,station,message,ack,source FROM alerts ORDER BY id DESC LIMIT 100').fetchall(); c.close()
 return [dict(zip(['id','created_at','type','severity','station','message','acknowledged','source'],r)) for r in rows]
def stations():
 ensure(); return pd.read_csv(DATA/'stations.csv').to_dict('records')
def trains():
 ensure(); df=pd.read_csv(DATA/'train_trips.csv'); now=datetime.now(); out=[]
 for _,r in df.iloc[-100:].iterrows():
  raw=pd.to_datetime(r.scheduled_time).to_pydatetime(); sched=raw.replace(year=now.year,month=now.month,day=now.day); delay=int(r.delay_minutes); actual=sched+pd.Timedelta(minutes=delay)
  out.append({'train_id':r.train_id,'line':r.line,'station':r.station,'scheduled_time':sched.isoformat(timespec='minutes'),'actual_time':actual.isoformat(timespec='minutes'),'delay_minutes':delay,'status':'On time' if delay<3 else ('Delayed' if delay<8 else 'Major delay'),'source':'synthetic timetable'})
 return sorted(out,key=lambda x:x['scheduled_time'])[:50]
def overview():
 ensure(); st=pd.read_csv(DATA/'stations.csv'); d=pd.read_csv(DATA/'ridership_hourly.csv'); h=datetime.now().hour; latest=d[d.hour==h].groupby('station_id',as_index=False)[['entries','exits']].mean()
 return {'stations':len(st),'passenger_entries':int(latest.entries.sum()),'passenger_exits':int(latest.exits.sum()),'network_crowd_proxy_pct':round(latest.entries.sum()/st.hourly_capacity.sum()*100,1),'active_alerts':sum(not a['acknowledged'] for a in get_alerts()),'scenario':SCENARIO,'simulation_running':RUNNING,'data_note':'Generated synthetic demo data; not a real metro feed.'}
def tick(scenario=None):
 global TICK,SCENARIO
 TICK+=1
 if scenario: SCENARIO=scenario
 st=pd.read_csv(DATA/'stations.csv'); rid=pd.read_csv(DATA/'ridership_hourly.csv'); h=datetime.now().hour; mult={'normal':1,'rush_hour':1.6,'demand_surge':2,'service_disruption':1.4}.get(SCENARIO,1); result=[]
 for _,s in st.iterrows():
  hist=rid[(rid.station_id==s.station_id)&(rid.hour==h)]; base=int(hist.entries.mean()) if len(hist) else int(s.hourly_capacity*.04); entries=int(base*mult*random.uniform(.9,1.1)); pct=round(min(100,entries/s.hourly_capacity*100),1)
  result.append({'station_id':s.station_id,'station':s.station,'line':s.line,'entries':entries,'capacity':int(s.hourly_capacity),'crowding_pct':pct})
  if pct>=85: alert('OVER_CROWDING','critical' if pct>=95 else 'high',s.station,f'Estimated crowd index {pct}% against capacity threshold 85%.')
 # Delay warnings only attach to explicit train records with schedule and simulated actual time.
 for tr in trains()[:20]:
  if tr['delay_minutes']>=7: alert('TRAIN_DELAY','critical' if tr['delay_minutes']>=12 else 'high',tr['station'],f"{tr['train_id']} is {tr['delay_minutes']} min after scheduled time {tr['scheduled_time']}.")
 return {'tick':TICK,'scenario':SCENARIO,'updated_at':datetime.now().isoformat(timespec='seconds'),'stations':result,'trains':trains()[:20],'alerts':get_alerts()[:30]}
def forecast(sid,horizon=6):
 ensure(); st=pd.read_csv(DATA/'stations.csv'); ids={v:i for i,v in enumerate(st.station_id)}
 if sid not in ids: raise ValueError('Unknown station')
 d=pd.read_csv(DATA/'ridership_hourly.csv'); X=d.assign(station_num=d.station_id.map(ids))[['station_num','hour','weekday','month']]; y=d.entries; split=int(len(d)*.8)
 path=DATA/'demand.joblib'
 if path.exists(): model=joblib.load(path)
 else:
  model=HistGradientBoostingRegressor(max_iter=70,random_state=42).fit(X.iloc[:split],y.iloc[:split]); joblib.dump(model,path)
 now=pd.Timestamp.now().floor('h'); out=[]
 for k in range(horizon):
  dt=now+pd.Timedelta(hours=k); x=pd.DataFrame([{'station_num':ids[sid],'hour':dt.hour,'weekday':dt.weekday(),'month':dt.month}]); val=max(0,int(model.predict(x)[0])); out.append({'time':dt.isoformat(),'hour':dt.hour,'predicted_entries':val,'low':int(val*.9),'high':int(val*1.1)})
 return out
def train_models():
 ensure(); d=pd.read_csv(DATA/'ridership_hourly.csv'); st=pd.read_csv(DATA/'stations.csv'); ids={v:i for i,v in enumerate(st.station_id)}; X=d.assign(station_num=d.station_id.map(ids))[['station_num','hour','weekday','month']]; y=d.entries; split=int(len(d)*.8)
 model=HistGradientBoostingRegressor(max_iter=70,random_state=42).fit(X.iloc[:split],y.iloc[:split]); mae=mean_absolute_error(y.iloc[split:],model.predict(X.iloc[split:])); joblib.dump(model,DATA/'demand.joblib')
 t=pd.read_csv(DATA/'train_trips.csv',parse_dates=['scheduled_time']); t['hour']=t.scheduled_time.dt.hour; t['rush']=t.hour.isin([7,8,9,17,18,19]).astype(int); t['crowd_proxy']=t.rush*.5+.3; Xd=t[['hour','rush','crowd_proxy']]; yd=(t.delay_minutes>=3).astype(int); clf=HistGradientBoostingClassifier(max_iter=50,random_state=42).fit(Xd,yd); joblib.dump(clf,DATA/'delay.joblib')
 return {'demand_holdout_MAE':round(float(mae),2),'delay_training_rows':len(t),'note':'Synthetic-data demonstration metrics; not real-world validation.'}
