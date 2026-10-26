"""API de eventos usada em todas as etapas do projeto."""

from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import Base, make_engine
from app.db_session import find_event, get_session
from app.models import Event, Registration


class EventInput(BaseModel):
    """Dados enviados pelo cliente ao cadastrar um evento."""

    title: str = Field(min_length=1)
    date: date
    capacity: int = Field(gt=0)


def event_to_dict(session: Session, event: Event) -> dict:
    """Monta a resposta de um evento, incluindo as vagas que ainda restam."""
    registered = session.scalar(
        select(func.count()).select_from(Registration).where(Registration.event_id == event.id)
    )
    return {
        "id": event.id,
        "title": event.title,
        "date": event.date,
        "capacity": event.capacity,
        "available_slots": event.capacity - registered,
    }


def create_app(database_url: str | None = None) -> FastAPI:
    """Cria uma API; sem URL, usa um banco em memória isolado para cada execução ou teste."""
    app = FastAPI(title="Eventos do Trilha")
    engine = make_engine(database_url or "sqlite://")
    Base.metadata.create_all(engine)
    app.state.engine = engine

    @app.get("/events")
    def list_events(session: Session = Depends(get_session)):
        events = session.scalars(select(Event).order_by(Event.id)).all()
        return [event_to_dict(session, event) for event in events]

    @app.get("/events/{event_id}")
    def get_event(event_id: int, session: Session = Depends(get_session)):
        event = find_event(session, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        return event_to_dict(session, event)

    @app.post("/events", status_code=201)
    def create_event(data: EventInput, session: Session = Depends(get_session)):
        event = Event(title=data.title, date=data.date, capacity=data.capacity)
        session.add(event)
        session.commit()
        return event_to_dict(session, event)

    return app

app = create_app("sqlite:///events.db")
