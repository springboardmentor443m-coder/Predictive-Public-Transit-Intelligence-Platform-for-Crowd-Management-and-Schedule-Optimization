from app.services import live_simulation


def test_simulated_live_requires_auth_and_admin_to_start(client, admin, operator):
    assert client.get('/simulation/live').status_code == 401
    assert client.post('/simulation/start', headers=operator).status_code == 403
    started = client.post('/simulation/start', headers=admin)
    assert started.status_code == 200, started.text
    body = started.json()
    assert body['running'] is True
    assert body['is_real_time'] is False
    assert body['mode'] == 'SIMULATED_LIVE'
    assert body['station_count'] == 30
    assert body['stations']
    assert all(row['is_simulated'] is True for row in body['stations'])


def test_operator_only_sees_assigned_station(client, admin, operator):
    client.post('/simulation/start', headers=admin)
    response = client.get('/simulation/live', headers=operator)
    assert response.status_code == 200
    body = response.json()
    assert body['station_count'] == 1
    assert body['stations'][0]['station'] == 'Taipei Main Station'


def test_stop_simulation(client, admin):
    client.post('/simulation/start', headers=admin)
    stopped = client.post('/simulation/stop', headers=admin)
    assert stopped.status_code == 200
    assert stopped.json()['running'] is False
    assert stopped.json()['is_real_time'] is False


def test_admin_can_change_simulation_scenario(client, admin, operator):
    client.post('/simulation/start', headers=admin)
    changed = client.post('/simulation/scenario', headers=admin, json={'scenario': 'service_disruption'})
    assert changed.status_code == 200, changed.text
    body = changed.json()
    assert body['scenario'] == 'service_disruption'
    assert body['running'] is True
    assert body['history']
    assert all('scenario' in point and 'alert_count' in point for point in body['history'])
    assert client.post('/simulation/scenario', headers=operator, json={'scenario': 'normal'}).status_code == 403


def test_invalid_scenario_is_rejected(client, admin):
    response = client.post('/simulation/scenario', headers=admin, json={'scenario': 'real_metro_feed'})
    assert response.status_code == 422
