"""
Script de seed — popula o banco com dados iniciais:
  - 3 usuários (admin, operador, visualizador)
  - 14 salas distribuídas em 3 andares
  - 1 dispositivo AC + sensores por sala (48 devices no total)

Uso:
  cd backend
  python -m scripts.seed_db
  # ou: DATABASE_URL=postgresql+asyncpg://... python -m scripts.seed_db
"""
from __future__ import annotations
import asyncio
import os
import sys
import uuid
from typing import List

# Garante que o diretório backend esteja no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models import *  # noqa — registra todos os modelos no metadata

# Converte URL sync → async se necessário
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not _db_url.startswith("postgresql+asyncpg://"):
    _db_url = _db_url

engine = create_async_engine(_db_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Dados de seed ───────────────────────────────────────────────────────────

USERS = [
    {"email": "admin@smartbuilding.local", "password": "admin123", "role": "admin"},
    {"email": "operador@smartbuilding.local", "password": "op123", "role": "operador"},
    {"email": "visualizador@smartbuilding.local", "password": "view123", "role": "visualizador"},
]

# 14 salas: 4 no andar 1, 5 no andar 2, 5 no andar 3
ROOMS = [
    # Andar 1
    {"name": "Sala 101 - TI", "building": "Bloco A", "floor": 1, "area_m2": 45.0},
    {"name": "Sala 102 - RH", "building": "Bloco A", "floor": 1, "area_m2": 30.0},
    {"name": "Sala 103 - Reuniões", "building": "Bloco A", "floor": 1, "area_m2": 25.0},
    {"name": "Sala 104 - Recepção", "building": "Bloco A", "floor": 1, "area_m2": 20.0},
    # Andar 2
    {"name": "Sala 201 - Diretoria", "building": "Bloco A", "floor": 2, "area_m2": 60.0},
    {"name": "Sala 202 - Financeiro", "building": "Bloco A", "floor": 2, "area_m2": 40.0},
    {"name": "Sala 203 - Jurídico", "building": "Bloco A", "floor": 2, "area_m2": 35.0},
    {"name": "Sala 204 - Marketing", "building": "Bloco A", "floor": 2, "area_m2": 40.0},
    {"name": "Sala 205 - Auditório", "building": "Bloco A", "floor": 2, "area_m2": 80.0},
    # Andar 3
    {"name": "Sala 301 - P&D", "building": "Bloco A", "floor": 3, "area_m2": 55.0},
    {"name": "Sala 302 - Laboratório", "building": "Bloco A", "floor": 3, "area_m2": 50.0},
    {"name": "Sala 303 - Suporte", "building": "Bloco A", "floor": 3, "area_m2": 30.0},
    {"name": "Sala 304 - Treinamento", "building": "Bloco A", "floor": 3, "area_m2": 45.0},
    {"name": "Sala 305 - Almoxarifado", "building": "Bloco A", "floor": 3, "area_m2": 25.0},
]

# Salas com sensor de presença (6 das 14)
PRESENCE_ROOMS = {0, 1, 4, 5, 9, 10}


async def seed(db: AsyncSession) -> None:
    from sqlalchemy import select, text
    from app.models.user import User, UserRole
    from app.models.room import Room
    from app.models.device import Device, DeviceType, DeviceStatus

    print("🌱 Iniciando seed do banco de dados...")

    # ── Usuários ────────────────────────────────────────────────────────────
    print("\n👤 Criando usuários...")
    for u_data in USERS:
        existing = (await db.execute(select(User).where(User.email == u_data["email"]))).scalar_one_or_none()
        if existing:
            print(f"   ⚠️  Usuário {u_data['email']} já existe, pulando.")
            continue
        user = User(
            id=uuid.uuid4(),
            email=u_data["email"],
            password_hash=hash_password(u_data["password"]),
            role=UserRole(u_data["role"]),
            is_active=True,
        )
        db.add(user)
        print(f"   ✅ {u_data['email']} ({u_data['role']})")
    await db.flush()

    # ── Salas e dispositivos ────────────────────────────────────────────────
    print("\n🏢 Criando salas e dispositivos...")
    for idx, r_data in enumerate(ROOMS):
        existing_room = (await db.execute(
            select(Room).where(Room.name == r_data["name"], Room.building == r_data["building"])
        )).scalar_one_or_none()

        if existing_room:
            room_id = existing_room.id
            print(f"   ⚠️  Sala '{r_data['name']}' já existe, pulando.")
        else:
            room = Room(id=uuid.uuid4(), **r_data)
            db.add(room)
            await db.flush()
            room_id = room.id
            print(f"   ✅ {r_data['name']} (andar {r_data['floor']})")

        # Verifica se já tem dispositivos nessa sala
        existing_devs = (await db.execute(
            select(Device).where(Device.room_id == room_id)
        )).scalars().all()
        if existing_devs:
            print(f"      ⚠️  Dispositivos para sala {room_id} já existem, pulando.")
            continue

        floor = r_data["floor"]
        room_num = idx + 1
        # AC
        db.add(Device(
            id=uuid.uuid4(), room_id=room_id,
            device_type=DeviceType.AC, model="Samsung WindFree AR12",
            serial_number=f"AC-{floor:02d}{room_num:02d}-001",
            status=DeviceStatus.OFFLINE, power_on=False, setpoint_celsius=24.0,
            mqtt_topic=f"devices/ac/AC-{floor:02d}{room_num:02d}-001/commands",
        ))
        # Sensor de temperatura
        db.add(Device(
            id=uuid.uuid4(), room_id=room_id,
            device_type=DeviceType.TEMPERATURE_SENSOR,
            serial_number=f"TEMP-{floor:02d}{room_num:02d}-001",
            status=DeviceStatus.OFFLINE,
            mqtt_topic=f"sensors/room/{room_id}/temperature",
        ))
        # Sensor de umidade
        db.add(Device(
            id=uuid.uuid4(), room_id=room_id,
            device_type=DeviceType.HUMIDITY_SENSOR,
            serial_number=f"UMID-{floor:02d}{room_num:02d}-001",
            status=DeviceStatus.OFFLINE,
            mqtt_topic=f"sensors/room/{room_id}/humidity",
        ))
        # Sensor de presença (apenas em algumas salas)
        if idx in PRESENCE_ROOMS:
            db.add(Device(
                id=uuid.uuid4(), room_id=room_id,
                device_type=DeviceType.PRESENCE_SENSOR,
                serial_number=f"PRES-{floor:02d}{room_num:02d}-001",
                status=DeviceStatus.OFFLINE,
                mqtt_topic=f"sensors/room/{room_id}/presence",
            ))

    await db.flush()
    await db.commit()
    print("\n✅ Seed concluído com sucesso!")
    print("\n📋 Resumo:")
    print(f"   • {len(USERS)} usuários")
    print(f"   • {len(ROOMS)} salas")
    device_count = len(ROOMS) * 3 + len(PRESENCE_ROOMS)
    print(f"   • {device_count} dispositivos (14 ACs + 14 temp + 14 umidade + 6 presença)")
    print("\n🔑 Credenciais:")
    for u in USERS:
        print(f"   {u['email']} / {u['password']} ({u['role']})")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        try:
            await seed(db)
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Erro durante o seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
