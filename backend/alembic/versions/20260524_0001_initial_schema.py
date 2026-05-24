"""Initial schema — sensor_data, users, rooms, alerts, audit_log

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-24 00:00:00

"""
from __future__ import annotations
from typing import Sequence, Union
from alembic import op

revision: str = "rev0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Usa SQL puro com IF NOT EXISTS / DO...EXCEPTION para idempotência total.

    # ── extensões PostgreSQL ──────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── sensor_data ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id BIGSERIAL PRIMARY KEY,
            sensor_id VARCHAR(50) NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            valor FLOAT NOT NULL,
            tick INTEGER NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            is_anomaly BOOLEAN NOT NULL DEFAULT false,
            received_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_sd_sensor_ts ON sensor_data(sensor_id, timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sd_tipo_ts   ON sensor_data(tipo, timestamp)")

    # ── user_role enum + users ────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('admin', 'operador', 'visualizador');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role user_role NOT NULL DEFAULT 'visualizador',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            UNIQUE (email)
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email)")

    # ── rooms ────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            building VARCHAR(100) NOT NULL,
            floor INTEGER NOT NULL,
            area_m2 FLOAT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
    """)

    # ── alert_type + alert_severity enums + alerts ────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alert_type AS ENUM (
                'HIGH_TEMPERATURE','LOW_HUMIDITY','ANOMALY_DETECTED',
                'DEVICE_OFFLINE','WINDOW_OPEN','CONSUMPTION_LIMIT'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alert_severity AS ENUM ('info','warning','critical');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_id UUID NOT NULL,
            alert_type alert_type NOT NULL,
            severity alert_severity NOT NULL,
            message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            acknowledged_at TIMESTAMPTZ,
            resolved_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_device_id ON alerts(device_id)")

    # ── audit_log ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(50),
            action VARCHAR(100) NOT NULL,
            resource VARCHAR(255),
            metadata_json JSONB,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_ts   ON audit_log(user_id, timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_action_ts ON audit_log(action, timestamp)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_log")
    op.execute("DROP TABLE IF EXISTS alerts")
    op.execute("DROP TABLE IF EXISTS rooms")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS sensor_data")
    op.execute("DROP TYPE IF EXISTS alert_severity")
    op.execute("DROP TYPE IF EXISTS alert_type")
    op.execute("DROP TYPE IF EXISTS user_role")
