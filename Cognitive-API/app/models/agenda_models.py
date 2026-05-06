from pydantic import BaseModel

class AgendaSlot(BaseModel):
    psicologo_id: int
    data_hora_iso: str

class Agendamento(BaseModel):
    agenda_id: int
    paciente_id: int