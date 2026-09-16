import time
import threading
from datetime import datetime, timedelta
import sqlite3
import os
from app.services.notifications import send_telegram_message, send_email_notification
from app.services.calendar import create_calendar_event

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database.sqlite"))

def check_ambitos_rules():
    while True:
        try:
            if os.path.exists(DB_FILE):
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM notes WHERE is_deleted = 0 AND realizada = 0")
                notes = [dict(row) for row in cursor.fetchall()]
                conn.close()

                today_str = datetime.now().strftime("%Y-%m-%d")
                tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

                for note in notes:
                    ambito = note.get("ambito")
                    titulo = note.get("titulo")
                    descripcion = note.get("descripcion") or ""
                    limite = note.get("limite") or note.get("fin") or note.get("fecha_abono")
                    estado = note.get("estado")

                    # Rule 1: 1 day before limit/fin/abono
                    if limite == tomorrow_str:
                        msg = f"⚠️ *WEB-HA Recordatorio (1 día antes)*\n*Ámbito:* {ambito}\n*Título:* {titulo}\nVence mañana: {limite}\n{descripcion}"
                        send_telegram_message(msg)
                        send_email_notification(f"[WEB-HA Vence Mañana] {ambito}: {titulo}", f"<p><b>Ámbito:</b> {ambito}</p><p><b>Título:</b> {titulo}</p><p><b>Vence mañana:</b> {limite}</p><p>{descripcion}</p>")

                    # Rule 2: On the limit date
                    if limite == today_str:
                        msg = f"🚨 *WEB-HA Alerta de Vencimiento Hoy*\n*Ámbito:* {ambito}\n*Título:* {titulo}\n*Límite Hoy:* {limite}\n{descripcion}"
                        send_telegram_message(msg)
                        send_email_notification(f"[WEB-HA Vence Hoy] {ambito}: {titulo}", f"<p><b>Ámbito:</b> {ambito}</p><p><b>Título:</b> {titulo}</p><p><b>Límite Hoy:</b> {limite}</p><p>{descripcion}</p>")
                        
                        # Register in Google Calendar at 08:00 hrs
                        create_calendar_event(
                            summary=f"[{ambito}] {titulo}",
                            description=descripcion,
                            limite_date=limite,
                            location=note.get("ubicacion")
                        )

                    # Rule 3: Estado POR PAGAR (Servicios / Plataformas)
                    if estado and estado.upper() == "POR PAGAR":
                        msg = f"💳 *WEB-HA Servicio/Deuda Pendiente*\n*Ámbito:* {ambito}\n*Título:* {titulo}\n*Estado:* {estado}\nMonto: ${note.get('monto') or note.get('abono') or 0}"
                        send_telegram_message(msg)

        except Exception as e:
            print(f"Error in scheduler check: {e}")

        # Check every 12 hours
        time.sleep(12 * 60 * 60)

def start_scheduler():
    t = threading.Thread(target=check_ambitos_rules, daemon=True)
    t.start()
    print("Background ambito rules scheduler started.")
