from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel

class NoteCreate(BaseModel):
    id: str
    ambito: str
    titulo: str
    descripcion: Optional[str] = None
    dependencias: Optional[str] = None
    ubicacion: Optional[str] = None
    enterado: Optional[str] = None
    limite: Optional[str] = None
    realizada: Optional[int] = 0
    monto: Optional[float] = None
    estado: Optional[str] = None
    inicio: Optional[str] = None
    fin: Optional[str] = None
    frecuencia: Optional[str] = None
    abono: Optional[float] = None
    restante: Optional[float] = None
    motivo: Optional[str] = None
    suscripcion: Optional[str] = None
    tipo: Optional[str] = "texto"
    archivo_url: Optional[str] = None
    transcripcion: Optional[str] = None
    updated_at: Optional[str] = None # ISO string from client
    is_deleted: Optional[int] = 0

class NoteResponse(BaseModel):
    id: str
    ambito: str
    titulo: str
    descripcion: Optional[str] = None
    dependencias: Optional[str] = None
    ubicacion: Optional[str] = None
    enterado: Optional[str] = None
    limite: Optional[str] = None
    realizada: int
    monto: Optional[float] = None
    estado: Optional[str] = None
    inicio: Optional[str] = None
    fin: Optional[str] = None
    frecuencia: Optional[str] = None
    abono: Optional[float] = None
    restante: Optional[float] = None
    motivo: Optional[str] = None
    suscripcion: Optional[str] = None
    tipo: str
    archivo_url: Optional[str] = None
    transcripcion: Optional[str] = None
    updated_at: datetime
    is_deleted: int

    class Config:
        from_attributes = True

class SyncRequest(BaseModel):
    notes: List[NoteCreate]

class SyncResponse(BaseModel):
    server_notes: List[NoteResponse]
    status: str = "success"
