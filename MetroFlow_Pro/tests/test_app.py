from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_health(): assert c.get('/health').json()['status']=='ok'
def test_station_count(): assert len(c.get('/api/stations').json())==30
def test_train_records_have_schedule():
 rows=c.get('/api/trains').json(); assert rows and all(r['train_id'] and r['scheduled_time'] and r['actual_time'] for r in rows)
def test_forecast():
 sid=c.get('/api/stations').json()[0]['station_id']; assert len(c.get(f'/api/forecast/{sid}?horizon_hours=3').json()['forecast'])==3
def test_simulation(): assert len(c.post('/api/simulation/tick',json={'scenario':'rush_hour'}).json()['stations'])==30
