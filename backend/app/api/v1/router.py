"""Agrega todos os routers da API v1."""

from fastapi import APIRouter

from app.api.v1 import auth, health, sensors, devices, rooms, alerts, users, consumption, predictions, reports

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(sensors.router)
api_router.include_router(devices.router)
api_router.include_router(rooms.router)
api_router.include_router(alerts.router)
api_router.include_router(users.router)
api_router.include_router(consumption.router)
api_router.include_router(predictions.router)
api_router.include_router(reports.router)
