import os
import shutil
import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.note import NoteModel
from app.schemas.note import NoteCreate, NoteResponse
from app.services.notifications import process_background_notifications
from app.services.whisper import transcribe_audio_file

router = APIRouter(prefix="/api/notes", tags=["notes"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[NoteResponse])
def get_notes(ambito: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(NoteModel).filter(NoteModel.is_deleted == 0)
    if ambito:
        query = query.filter(NoteModel.ambito == ambito)
    return query.all()

@router.post("/", response_model=NoteResponse)
def create_or_update_note(
    background_tasks: BackgroundTasks,
    note: NoteCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(NoteModel).filter(NoteModel.id == note.id).first()
    
    parsed_updated_at = datetime.utcnow()
    if note.updated_at:
        try:
            parsed_updated_at = datetime.fromisoformat(note.updated_at.replace("Z", "+00:00"))
        except:
            pass

    if existing:
        # Last-write-wins comparison
        existing.ambito = note.ambito
        existing.titulo = note.titulo
        existing.descripcion = note.descripcion
        existing.dependencias = note.dependencias
        existing.ubicacion = note.ubicacion
        existing.enterado = note.enterado
        existing.limite = note.limite
        existing.realizada = note.realizada if note.realizada is not None else existing.realizada
        existing.monto = note.monto
        existing.estado = note.estado
        existing.inicio = note.inicio
        existing.fin = note.fin
        existing.frecuencia = note.frecuencia
        existing.abono = note.abono
        existing.restante = note.restante
        existing.motivo = note.motivo
        existing.suscripcion = note.suscripcion
        existing.tipo = note.tipo
        existing.archivo_url = note.archivo_url or existing.archivo_url
        existing.transcripcion = note.transcripcion or existing.transcripcion
        existing.updated_at = parsed_updated_at
        existing.is_deleted = note.is_deleted if note.is_deleted is not None else existing.is_deleted
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_note = NoteModel(
            id=note.id,
            ambito=note.ambito,
            titulo=note.titulo,
            descripcion=note.descripcion,
            dependencias=note.dependencias,
            ubicacion=note.ubicacion,
            enterado=note.enterado,
            limite=note.limite,
            realizada=note.realizada or 0,
            monto=note.monto,
            estado=note.estado,
            inicio=note.inicio,
            fin=note.fin,
            frecuencia=note.frecuencia,
            abono=note.abono,
            restante=note.restante,
            motivo=note.motivo,
            suscripcion=note.suscripcion,
            tipo=note.tipo or "texto",
            archivo_url=note.archivo_url,
            transcripcion=note.transcripcion,
            updated_at=parsed_updated_at,
            is_deleted=note.is_deleted or 0
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)

        # Trigger background notifications
        background_tasks.add_task(
            process_background_notifications,
            ambito=db_note.ambito,
            titulo=db_note.titulo,
            descripcion=db_note.descripcion,
            limite=db_note.limite
        )

        return db_note

@router.delete("/{note_id}")
def delete_note(note_id: str, db: Session = Depends(get_db)):
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.is_deleted = 1
    note.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "deleted"}

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    timestamp = int(time.time() * 1000)
    filename = f"audio_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Transcribe audio using faster-whisper locally
    transcription = transcribe_audio_file(file_path)
    
    return {
        "file_url": f"/uploads/{filename}",
        "transcription": transcription
    }
