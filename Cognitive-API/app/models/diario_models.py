from pydantic import BaseModel
from typing import List


class DiarioEntry(BaseModel):
    paciente_id: int
    data_hora_iso: str
    sentimento_id: int
    anotacao: str
    atividades_ids: List[int]
