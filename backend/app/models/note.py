from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.database import Base

class NoteModel(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, index=True) # UUID from client
    ambito = Column(String, index=True, nullable=False) # Personal, Trabajo, Tramites, Plataformas, Servicios, Deudas, Avisos, Constantes
    
    # Common / Ambito specific fields
    titulo = Column(String, nullable=False) # ObjetivoPersonal, Servicio, Deuda, Aviso, Constante, etc.
    descripcion = Column(Text, nullable=True)
    dependencias = Column(Text, nullable=True)
    ubicacion = Column(String, nullable=True)
    enterado = Column(String, nullable=True)
    limite = Column(String, nullable=True)
    realizada = Column(Integer, default=0) # 0: Pending, 1: Done

    # Specific fields
    monto = Column(Float, nullable=True)
    estado = Column(String, nullable=True)
    inicio = Column(String, nullable=True)
    fin = Column(String, nullable=True)
    frecuencia = Column(String, nullable=True)
    abono = Column(Float, nullable=True)
    restante = Column(Float, nullable=True)
    motivo = Column(Text, nullable=True)
    suscripcion = Column(String, nullable=True)

    # Media / Audio
    tipo = Column(String, default="texto") # texto, lista, imagen, audio
    archivo_url = Column(String, nullable=True)
    transcripcion = Column(Text, nullable=True)

    # Sync and audit
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Integer, default=0)
