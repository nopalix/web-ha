from app.services.notifications import process_background_notifications

if __name__ == "__main__":
    print("Testing notifications (Telegram, Email, Google Calendar)...")
    process_background_notifications(
        ambito="Trabajo",
        titulo="Prueba de automatización WEB-HA",
        descripcion="Revisión de funcionamiento de envíos automáticos para TDAH.",
        limite="2026-09-01"
    )
    print("Test execution finished.")
