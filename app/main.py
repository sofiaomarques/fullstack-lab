"""API de eventos usada em todas as etapas do projeto."""

from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import models  # noqa: F401  (registra as tabelas em Base.metadata)
from app.database import Base, make_engine


class EventInput(BaseModel):
    """Dados enviados pelo cliente ao cadastrar um evento."""

    title: str = Field(min_length=1)
    date: date
    capacity: int = Field(gt=0)


def create_app(database_url: str | None = None) -> FastAPI:
    """Cria uma API; sem URL, usa um banco em memória isolado para cada execução ou teste."""
    app = FastAPI(title="Eventos do Trilha")
    engine = make_engine(database_url or "sqlite://")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    events: dict[int, dict] = {}

    @app.get("/events")
    def list_events():
        return list(events.values())

    @app.get("/events/{event_id}")
    def get_event(event_id: int):
        event = events.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        return event

    @app.post("/events", status_code=201)
    def create_event(data: EventInput):
        event_id = len(events) + 1
        event = {
            "id": event_id,
            "title": data.title,
            "date": data.date,
            "capacity": data.capacity,
        }
        events[event_id] = event
        return event

    return app

app = create_app("sqlite:///events.db")
