from datetime import date, time
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Project(BaseModel):
    mode: Literal['guided', 'direct'] = 'guided'
    origin: str = Field(min_length=2, max_length=200)
    origin_station: str | None = None
    destination_id: str | None = None
    destination_station: str | None = None
    theme: str = Field(default='Moyen Âge', max_length=200)
    level: str = Field(default='5e', max_length=40)
    students: int = Field(default=28, ge=1, le=200)
    companions: int = Field(default=2, ge=1, le=50)
    group_total: int | None = Field(default=None, ge=6, le=200)
    date: date
    trip_type: Literal['round_trip', 'one_way'] = 'round_trip'
    earliest: time = time(8)
    latest: time = time(19)
    visit_minutes: int = Field(default=120, ge=30, le=480)
    origin_access_minutes: int = Field(default=15, ge=0, le=180)
    scenario: Literal['normal', 'busy'] = 'normal'

    @property
    def group_size(self):
        return self.group_total if self.group_total is not None else self.students + self.companions

    @model_validator(mode='after')
    def coherent(self):
        if self.earliest >= self.latest:
            raise ValueError('L’heure limite doit être après l’heure de départ.')
        if self.mode == 'direct' and not self.destination_id and not self.destination_station:
            raise ValueError('Choisissez une destination ou une gare d’arrivée.')
        return self


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    fields: dict = Field(default_factory=dict)
    history: list['ChatTurn'] = Field(default_factory=list, max_length=12)


class ChatTurn(BaseModel):
    role: Literal['user','assistant']
    text: str = Field(max_length=4000)


class OptionRequest(BaseModel):
    proposal_id: str
    idempotency_key: str = Field(min_length=8, max_length=100)


class PrereservationRequest(BaseModel):
    dossier_id: str
    teacher_name: str = Field(min_length=2, max_length=100)
    school: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=200)

    @model_validator(mode='after')
    def validate_email(self):
        import re
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', self.email):
            raise ValueError('Adresse e-mail invalide.')
        return self
