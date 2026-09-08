"""Initial schema for MetroFlow: stations, ridership_logs, train_status, alerts

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-05 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'stations' table
    # SQL: CREATE TABLE stations (station_code VARCHAR(32) PRIMARY KEY, name_en VARCHAR(100) NOT NULL, name_kr VARCHAR(100), line VARCHAR(50) NOT NULL, latitude FLOAT NOT NULL, longitude FLOAT NOT NULL, district VARCHAR(100));
    op.create_table(
        "stations",
        sa.Column("station_code", sa.String(length=32), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=False),
        sa.Column("name_kr", sa.String(length=100), nullable=True),
        sa.Column("line", sa.String(length=50), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("station_code"),
    )
    op.create_index("ix_stations_station_code", "stations", ["station_code"])
    op.create_index("ix_stations_name_en", "stations", ["name_en"])
    op.create_index("ix_stations_line", "stations", ["line"])

    # 2. Create 'ridership_logs' table
    # SQL: CREATE TABLE ridership_logs (id SERIAL PRIMARY KEY, station_code VARCHAR(32) REFERENCES stations(station_code) ON DELETE CASCADE, timestamp TIMESTAMP WITH TIME ZONE NOT NULL, hour INTEGER NOT NULL, day_of_week INTEGER NOT NULL, is_weekend BOOLEAN NOT NULL, inflow INTEGER NOT NULL, outflow INTEGER NOT NULL);
    op.create_table(
        "ridership_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("station_code", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hour", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("is_weekend", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("inflow", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outflow", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["station_code"], ["stations.station_code"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ridership_logs_station_code", "ridership_logs", ["station_code"])
    op.create_index("ix_ridership_logs_timestamp", "ridership_logs", ["timestamp"])
    op.create_index("idx_ridership_station_time", "ridership_logs", ["station_code", "timestamp"])
    op.create_index("idx_ridership_hour_dow", "ridership_logs", ["hour", "day_of_week"])

    # 3. Create 'train_status' table
    # SQL: CREATE TABLE train_status (id SERIAL PRIMARY KEY, line VARCHAR(50) NOT NULL, timestamp TIMESTAMP WITH TIME ZONE NOT NULL, occupancy_pct FLOAT NOT NULL, delay_minutes INTEGER NOT NULL DEFAULT 0);
    op.create_table(
        "train_status",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("line", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("occupancy_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("delay_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_train_status_line", "train_status", ["line"])
    op.create_index("ix_train_status_timestamp", "train_status", ["timestamp"])
    op.create_index("idx_train_status_line_time", "train_status", ["line", "timestamp"])

    # 4. Create 'alerts' table
    # SQL: CREATE TABLE alerts (id SERIAL PRIMARY KEY, station_code VARCHAR(32) REFERENCES stations(station_code) ON DELETE CASCADE, alert_type VARCHAR(30) NOT NULL, severity VARCHAR(20) NOT NULL, message TEXT NOT NULL, created_at TIMESTAMP WITH TIME ZONE NOT NULL, resolved BOOLEAN NOT NULL DEFAULT FALSE);
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("station_code", sa.String(length=32), nullable=True),
        sa.Column("alert_type", sa.String(length=30), nullable=False, server_default="overcrowding"),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["station_code"], ["stations.station_code"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_station_code", "alerts", ["station_code"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index("ix_alerts_resolved", "alerts", ["resolved"])
    op.create_index("idx_alert_severity_resolved", "alerts", ["severity", "resolved"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("train_status")
    op.drop_table("ridership_logs")
    op.drop_table("stations")
