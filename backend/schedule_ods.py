import os
import sqlite3
from datetime import datetime
from app.services.calendar import create_calendar_event

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "database.sqlite"))

def parse_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # Try YYYY-MM-DD
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    # Try DD-MM-YYYY
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    return None

def schedule_all_pending():
    if not os.path.exists(DB_FILE):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE is_deleted = 0 AND realizada = 0")
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()

    print(f"Encontradas {len(notes)} notas pendientes para programar en Google Calendar...")

    count = 0
    for note in notes:
        ambito = note.get("ambito")
        titulo = note.get("titulo")
        descripcion = note.get("descripcion") or ""
        ubicacion = note.get("ubicacion")
        raw_limit = note.get("limite") or note.get("fin") or note.get("fecha_abono")
        
        limite = parse_date(raw_limit)
        if limite:
            summary = f"[{ambito}] {titulo}"
            print(f"Agendando: {summary} para el {limite}...")
            create_calendar_event(
                summary=summary,
                description=descripcion,
                limite_date=limite,
                location=ubicacion
            )
            count += 1

    print(f"¡Proceso de agendamiento masivo finalizado! Se intentó programar {count} eventos en Google Calendar.")

if __name__ == "__main__":
    schedule_all_pending()
