"""Add devices, commands, predictions tables

Revision ID: 0002_devices_commands_predictions
Revises: 0001_initial
Create Date: 2026-05-24 12:00:00

"""
from __future__ import annotations
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "rev0002"
down_revision: Union[str, None] = "rev0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── device_type enum ──────────────────────────────────────
    # Usa DO/EXCEPTION para ignorar se o tipo já existir
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE device_type AS ENUM
                ('ac','temperature_sensor','humidity_sensor','presence_sensor','window_sensor');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE device_status AS ENUM ('online','offline','maintenance');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── devices ───────────────────────────────────────────────
    # Cria tabela somente se não existir
    op.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id UUID PRIMARY KEY,
            room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
            device_type device_type NOT NULL,
            model VARCHAR(100),
            serial_number VARCHAR(100) UNIQUE,
            status device_status NOT NULL DEFAULT 'offline',
            is_active BOOLEAN NOT NULL DEFAULT true,
            power_on BOOLEAN NOT NULL DEFAULT false,
            setpoint_celsius FLOAT,
            mqtt_topic VARCHAR(200),
            notes TEXT,
            last_seen_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_devices_room_id ON devices(room_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_devices_status ON devices(status)")

    # ── command_type / command_status enums ───────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE command_type AS ENUM
                ('power_on','power_off','set_temperature','set_mode');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE command_status AS ENUM ('pending','sent','executed','failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── commands ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id UUID PRIMARY KEY,
            device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
            issued_by VARCHAR(50),
            command_type command_type NOT NULL,
            value FLOAT,
            payload_json TEXT,
            status command_status NOT NULL DEFAULT 'pending',
            executed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_commands_device_id ON commands(device_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_commands_created_at ON commands(created_at)")

    # ── predictions ───────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id UUID PRIMARY KEY,
            device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
            predicted_consumption_kwh FLOAT NOT NULL,
            actual_consumption_kwh FLOAT,
            confidence FLOAT,
            horizon_hours INTEGER NOT NULL DEFAULT 24,
            prediction_for TIMESTAMPTZ NOT NULL,
            model_version TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_predictions_device_pred_for ON predictions(device_id, prediction_for)")

    # ── fix alerts FK to devices ─────────────────────────────
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE alerts ADD CONSTRAINT fk_alerts_device_id
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.drop_constraint("fk_alerts_device_id", "alerts", type_="foreignkey")
    op.drop_table("predictions")
    op.drop_table("commands")
    op.drop_table("devices")
    op.execute("DROP TYPE IF EXISTS command_status")
    op.execute("DROP TYPE IF EXISTS command_type")
    op.execute("DROP TYPE IF EXISTS device_status")
    op.execute("DROP TYPE IF EXISTS device_type")
