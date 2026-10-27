"""Service Health API — a small FastAPI app deployed to an Azure VM.

It keeps an in-memory registry of services a team wants to watch and
exposes health and Prometheus metrics. It is intentionally stateless:
restarting the container resets the registry, which is fine for a
demo and keeps the deployment simple (no database to manage).
"""
import uuid

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response

app = FastAPI(title="Service Health API", version="1.0.0")

services: dict[str, dict] = {}
services_created_total = Counter("services_created_total", "Total services registered")
services_total = Gauge("services_total", "Services currently registered")


class ServiceIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    description: str = ""


@app.get("/")
def root():
    return {"service": "Service Health API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    services_total.set(len(services))
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/services")
def list_services():
    return list(services.values())


@app.post("/api/services", status_code=201)
def create_service(payload: ServiceIn):
    service_id = str(uuid.uuid4())
    service = {"id": service_id, **payload.model_dump(), "status": "unknown"}
    services[service_id] = service
    services_created_total.inc()
    services_total.set(len(services))
    return service


@app.get("/api/services/{service_id}")
def get_service(service_id: str):
    if service_id not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    return services[service_id]


@app.delete("/api/services/{service_id}", status_code=204)
def delete_service(service_id: str):
    if service_id not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    del services[service_id]
    services_total.set(len(services))
    return None
