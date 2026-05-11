from pydantic import BaseModel


class VinculoData(BaseModel):
    paciente_id: int
    codigo: str


class ConviteEmail(BaseModel):
    email_paciente: str
    psicologo_id: int


class AtividadeTemplate(BaseModel):
    texto: str
    psicologo_id: int


class ConsultaNota(BaseModel):
    psicologo_id: int
    paciente_id: int
    anotacao: str
    data_hora_iso: str
