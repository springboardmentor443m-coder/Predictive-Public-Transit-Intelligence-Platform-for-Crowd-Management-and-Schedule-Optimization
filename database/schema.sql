

CREATE TABLE IF NOT EXISTS crowd_evacuation (
    id SERIAL PRIMARY KEY,
    scenario VARCHAR(100),
    sensor_type VARCHAR(100),
    occupancy_count INTEGER,
    crowd_density_level DECIMAL(10,3),
    detection_time_sec DECIMAL(10,3),
    peak_hazard_exposure_percent DECIMAL(10,2),
    evacuation_time_sec DECIMAL(10,2),
    success_rate_percent DECIMAL(10,2),
    decision_node VARCHAR(100),
    adaptive_route_id INTEGER,
    flow_pattern_score DECIMAL(10,3),
    evacuation_strategy_type VARCHAR(100),
    comment TEXT,
    occupancy_normalized DECIMAL(10,4),
    density_normalized DECIMAL(10,4),
    hazard_normalized DECIMAL(10,4),
    combined_avg DECIMAL(10,4),
    route_status VARCHAR(50)
);


CREATE TABLE IF NOT EXISTS nyc_subway_traffic (
    id BIGSERIAL PRIMARY KEY,
    unique_id BIGINT,
    datetime TIMESTAMP,
    stop_name VARCHAR(150),
    remote_unit VARCHAR(50),
    line VARCHAR(100),
    connecting_lines VARCHAR(100),
    daytime_routes VARCHAR(100),
    division VARCHAR(50),
    structure VARCHAR(50),
    borough VARCHAR(50),
    neighborhood VARCHAR(150),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    entries BIGINT,
    exits BIGINT
);


CREATE TABLE IF NOT EXISTS mta_hourly_ridership (
    id BIGSERIAL PRIMARY KEY,
    transit_timestamp TIMESTAMP,
    station_complex_id VARCHAR(50),
    station_complex VARCHAR(200),
    borough VARCHAR(50),
    routes VARCHAR(100),
    payment_method VARCHAR(50),
    ridership BIGINT,
    transfers BIGINT,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    georeference TEXT
);


CREATE TABLE IF NOT EXISTS metro_transactions (
    id BIGSERIAL PRIMARY KEY,
    time TIMESTAMP,
    line_id VARCHAR(50),
    station_id VARCHAR(50),
    device_id VARCHAR(50),
    status VARCHAR(50),
    user_id VARCHAR(100),
    pay_type VARCHAR(50)
);


CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer'
);



CREATE INDEX IF NOT EXISTS idx_crowd_scenario
ON crowd_evacuation(scenario);

CREATE INDEX IF NOT EXISTS idx_crowd_route_status
ON crowd_evacuation(route_status);



CREATE INDEX IF NOT EXISTS idx_nyc_datetime
ON nyc_subway_traffic(datetime);

CREATE INDEX IF NOT EXISTS idx_nyc_stop
ON nyc_subway_traffic(stop_name);



CREATE INDEX IF NOT EXISTS idx_mta_timestamp
ON mta_hourly_ridership(transit_timestamp);

CREATE INDEX IF NOT EXISTS idx_mta_station
ON mta_hourly_ridership(station_complex_id);



CREATE INDEX IF NOT EXISTS idx_metro_time
ON metro_transactions(time);

CREATE INDEX IF NOT EXISTS idx_metro_station
ON metro_transactions(station_id);



CREATE INDEX IF NOT EXISTS idx_users_username
ON users(username);