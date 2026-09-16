# Bitácora de Cambios - WEB-HA

## [2026-08-31] - Versión Inicial y Automatización Completa
- **Arquitectura Local-First / PWA:** Estructura modular con Backend (FastAPI / Pure Python HTTP Server con SQLite) y Frontend (HTML5, Tailwind CSS, IndexedDB, Service Worker).
- **Ámbitos Soportados:** Personal, Trabajo, Trámites, Plataformas, Servicios, Deudas, Avisos y Constantes.
- **Transcripción de Audio Local:** Integración con `faster-whisper` para procesar notas de voz.
- **Sincronización Offline:** Almacenamiento local con IndexedDB y sincronización automática online/offline basada en la política "Última actualización gana".
- **Notificaciones Externas:**
  - Envío de mensajes vía Telegram Bot (`/sendMessage`).
  - Envío de correos HTML mediante SMTP (`smtplib`).
  - Creación automática de eventos en Google Calendar (OAuth2 / cuenta principal) a las 08:00 hrs para tareas con fecha límite.
- **Corrección de Flujo de Sincronización:** Se actualizó el endpoint de sincronización `/api/sync` para disparar notificaciones en segundo plano (Telegram, Email, Calendar) al registrar nuevas tareas desde la PWA.
- **Autorización OAuth2 de Google Calendar:** Creación del script auxiliar `backend/authorize_calendar.py` para generar el token de acceso interactivo (`token.json`).
- **Programador de Tareas Diario (Scheduler):** Integración de un servicio en segundo plano (`backend/app/services/scheduler.py`) que evalúa diariamente las reglas de los ámbitos (avisos 1 día antes, día límite, estado "POR PAGAR", etc.).
- **Importación de Registros Reales (`DetallesAmbitos.ods`):** Creación del script de importación `backend/import_ods.py` para parsear el archivo ODS y registrar automáticamente todas las actividades reales en los diferentes ámbitos en la base de datos SQLite.
- **Funcionalidad de Edición de Registros:** Incorporación del botón "Editar" en las tarjetas de notas del frontend, precargando el modal con la información existente y actualizando el registro manteniendo su ID original (Last-Write-Wins).
- **Estilos Visuales para Tareas Completadas (v1.3.0):** Al marcar una tarea como "Realizada", el sistema aplica automáticamente estilos de tachado (`line-through`), reducción de opacidad y reordena automáticamente la lista para colocar las tareas completadas al final.
