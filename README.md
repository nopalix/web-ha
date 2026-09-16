# WEB-HA: Asistente Personal Local-First (TDAH)

Sistema de gestión de tareas y notas personalizado, diseñado con enfoque **Local-First / Offline-First / PWA**, ideal para registrar ideas, pendientes y estructurar la información personal y profesional (inspirado en Google Keep, adaptado para personas con TDAH).

---

## 🛠️ Arquitectura y Tecnologías

- **Backend:** Python (FastAPI / Servidor HTTP asíncrono nativo con SQLite y SQLAlchemy).
- **Frontend / PWA:** HTML5, Tailwind CSS (vía CDN), JavaScript Modular (Vainilla) con Progressive Web App (Service Worker + IndexedDB).
- **Transcripción de Audio:** Procesamiento local con `faster-whisper`.
- **Integraciones Externas:**
  - **Telegram Bot:** Alertas automáticas y recordatorios (`requests`).
  - **Correo Electrónico:** Notificaciones HTML vía SMTP (`smtplib`).
  - **Google Calendar API:** Agendamiento automático de vencimientos a las 08:00 hrs (OAuth2).

---

## 📂 Estructura de Carpetas

```text
web-ha/
├── backend/
│   ├── app/
│   │   ├── models/          # Modelos de base de datos SQLAlchemy
│   │   ├── routers/         # Endpoints REST (notas, sincronización)
│   │   └── services/        # Servicios de notificaciones, Whisper y Calendar
│   ├── uploads/             # Archivos multimedia (audio/imagen con timestamp)
│   ├── database.sqlite      # Base de datos local SQLite
│   ├── requirements.txt     # Dependencias de Python
│   └── .env                 # Variables de entorno y credenciales
├── frontend/
│   ├── js/                  # Módulos JS (app, db, sync, audio)
│   ├── index.html           # SPA minimalista y UI moderna
│   ├── manifest.json        # Manifiesto PWA
│   └── sw.js                # Service Worker para modo offline
├── docs/
│   └── bitacora.md          # Bitácora de cambios y versiones
├── DetallesAmbitos.ods      # Registros reales iniciales
└── README.md
```

---

## ⚙️ Configuración y Puesta en Marcha

1. **Instalar dependencias de Python:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configurar el archivo de entorno (`backend/.env`):**
   Crea o edita el archivo `.env` en la carpeta `backend/` con tus credenciales:
   ```env
   TELEGRAM_BOT_TOKEN=tu_token_aqui
   TELEGRAM_CHAT_ID=tu_chat_id_aqui
   SMTP_USER=tu_correo@gmail.com
   SMTP_PASSWORD=tu_contraseña_de_aplicacion
   EMAIL_TO=correo_destino@gmail.com
   GOOGLE_CREDENTIALS_FILE=credentials.json
   ```

3. **Ejecutar el servidor local:**
   ```bash
   PYTHONPATH=. python3 -m app.main
   ```

4. **Acceder a la aplicación:**
   Abre tu navegador en **`http://localhost:8001`**.

---

## 🔄 Sincronización y Reglas de Ámbitos
- **Sincronización Offline:** Funciona sin conexión almacenando en IndexedDB y sincroniza automáticamente al recuperar red utilizando la política **"Última actualización gana" (Last-Write-Wins)**.
- **Reglas de Negocio:** Evalúa ámbitos como *Trabajo*, *Trámites*, *Personal*, *Plataformas*, *Servicios*, *Deudas*, *Avisos* y *Constantes*, enviando recordatorios 1 día antes y el día límite.
