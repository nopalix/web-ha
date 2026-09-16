import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from app.config import settings
from app.services.calendar import create_calendar_event

def send_telegram_message(message: str):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("Telegram settings not configured.")
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def send_email_notification(subject: str, body: str):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD or not settings.EMAIL_TO:
        print("SMTP settings not configured.")
        return
    
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USER
    msg['To'] = settings.EMAIL_TO
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, settings.EMAIL_TO, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

def process_background_notifications(ambito: str, titulo: str, descripcion: str, limite: str):
    msg_text = f"🔔 *WEB-HA Notificación*\n*Ámbito:* {ambito}\n*Título:* {titulo}\n*Límite:* {limite or 'Sin límite'}\n*Detalle:* {descripcion or ''}"
    send_telegram_message(msg_text)
    
    email_body = f"<h2>Nueva Tarea / Aviso Registrado</h2><p><b>Ámbito:</b> {ambito}</p><p><b>Título:</b> {titulo}</p><p><b>Límite:</b> {limite}</p><p><b>Descripción:</b> {descripcion}</p>"
    send_email_notification(f"[WEB-HA] {ambito}: {titulo}", email_body)

    if limite:
        create_calendar_event(
            summary=f"[{ambito}] {titulo}",
            description=descripcion or "",
            limite_date=limite
        )
