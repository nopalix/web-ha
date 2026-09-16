from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.note import NoteModel
from app.schemas.note import SyncRequest, SyncResponse, NoteResponse

router = APIRouter(prefix="/api/sync", tags=["sync"])

@router.post("/", response_model=SyncResponse)
def sync_notes(payload: SyncRequest, db: Session = Depends(get_db)):
    client_notes = payload.notes
    
    for c_note in client_notes:
        existing = db.query(NoteModel).filter(NoteModel.id == c_note.id).first()
        
        c_updated = datetime.utcnow()
        if c_note.updated_at:
            try:
                c_updated = datetime.fromisoformat(c_note.updated_at.replace("Z", "+00:00"))
            except:
                pass

        if existing:
            # Last write wins conflict resolution
            if c_updated >= existing.updated_at:
                existing.ambito = c_note.ambito
                existing.titulo = c_note.titulo
                existing.descripcion = c_note.descripcion
                existing.dependencias = c_note.dependencias
                existing.ubicacion = c_note.ubicacion
                existing.enterado = c_note.enterado
                existing.limite = c_note.limite
                existing.realizada = c_note.realizada if c_note.realizada is not None else existing.realizada
                existing.monto = c_note.monto
                existing.estado = c_note.estado
                existing.inicio = c_note.inicio
                existing.fin = c_note.fin
                existing.frecuencia = c_note.frecuencia
                existing.abono = c_note.abono
                existing.restante = c_note.restante
                existing.motivo = c_note.motivo
                existing.suscripcion = c_note.suscripcion
                existing.tipo = c_note.tipo
                existing.archivo_url = c_note.archivo_url or existing.archivo_url
                existing.transcripcion = c_note.transcripcion or existing.transcripcion
                existing.updated_at = c_updated
                existing.is_deleted = c_note.is_deleted if c_note.is_deleted is not None else existing.is_deleted
        else:
            db_note = NoteModel(
                id=c_note.id,
                ambito=c_note.ambito,
                titulo=c_note.titulo,
                descripcion=c_note.descripcion,
                dependencias=c_note.dependencias,
                ubicacion=c_note.ubicacion,
                enterado=c_note.enterado,
                limite=c_note.limite,
                realizada=c_note.realizada or 0,
                monto=c_note.monto,
                estado=c_note.estado,
                inicio=c_note.inicio,
                fin=c_note.fin,
                frecuencia=c_note.frecuencia,
                abono=c_note.abono,
                restante=c_note.restante,
                motivo=c_note.motivo,
                suscripcion=c_note.suscripcion,
                tipo=c_note.tipo or "texto",
                archivo_url=c_note.archivo_url,
                transcripcion=c_note.transcripcion,
                updated_at=c_updated,
                is_deleted=c_note.is_deleted or 0
            )
            db.add(db_note)
            
    db.commit()
    
    # Return all server notes so client can update its local DB
    server_notes = db.query(NoteModel).all()
    return {
        "server_notes": server_notes,
        "status": "success"
    }
