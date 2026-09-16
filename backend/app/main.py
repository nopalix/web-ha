import http.server
import socketserver
import os
import json
import sqlite3
import urllib.parse
import time
import threading
from datetime import datetime
from app.services.notifications import process_background_notifications
from app.services.scheduler import start_scheduler

PORT = 8001
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database.sqlite"))
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))

os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    print("USING DB_FILE:", DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            ambito TEXT NOT NULL,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            dependencias TEXT,
            ubicacion TEXT,
            enterado TEXT,
            limite TEXT,
            realizada INTEGER DEFAULT 0,
            monto REAL,
            estado TEXT,
            inicio TEXT,
            fin TEXT,
            frecuencia TEXT,
            abono REAL,
            restante REAL,
            motivo TEXT,
            suscripcion TEXT,
            tipo TEXT DEFAULT 'texto',
            archivo_url TEXT,
            transcripcion TEXT,
            updated_at TEXT,
            is_deleted INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class WebHAHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if path == "/api/health":
            self.send_json({"status": "healthy", "service": "WEB-HA Pure Python API"})
            return

        if path == "/api/notes":
            ambito = query_params.get("ambito", [None])[0]
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if ambito and ambito != "Todos":
                cursor.execute("SELECT * FROM notes WHERE is_deleted = 0 AND ambito = ?", (ambito,))
            else:
                cursor.execute("SELECT * FROM notes WHERE is_deleted = 0")
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_json(rows)
            return

        # Serve static files from frontend or uploads
        if path.startswith("/uploads/"):
            filepath = os.path.join(".", path.lstrip("/"))
            if os.path.exists(filepath):
                self.serve_file(filepath)
                return

        # Serve frontend
        if path == "/" or path == "":
            filepath = os.path.join(FRONTEND_DIR, "index.html")
        else:
            filepath = os.path.join(FRONTEND_DIR, path.lstrip("/"))

        if os.path.exists(filepath) and os.path.isfile(filepath):
            self.serve_file(filepath)
        else:
            # Fallback to index.html for SPA routing
            index_path = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.exists(index_path):
                self.serve_file(index_path)
            else:
                self.send_error(404, "File not found")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/api/notes":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                self.send_json({"error": "Invalid JSON"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            note_id = data.get("id")
            updated_at = data.get("updated_at") or datetime.utcnow().isoformat()

            cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute('''
                    UPDATE notes SET
                        ambito = ?, titulo = ?, descripcion = ?, dependencias = ?, ubicacion = ?,
                        enterado = ?, limite = ?, realizada = ?, monto = ?, estado = ?, inicio = ?,
                        fin = ?, frecuencia = ?, abono = ?, restante = ?, motivo = ?, suscripcion = ?,
                        tipo = ?, archivo_url = COALESCE(?, archivo_url), transcripcion = COALESCE(?, transcripcion),
                        updated_at = ?, is_deleted = ?
                    WHERE id = ?
                ''', (
                    data.get("ambito"), data.get("titulo"), data.get("descripcion"),
                    data.get("dependencias"), data.get("ubicacion"), data.get("enterado"),
                    data.get("limite"), data.get("realizada", 0), data.get("monto"),
                    data.get("estado"), data.get("inicio"), data.get("fin"),
                    data.get("frecuencia"), data.get("abono"), data.get("restante"),
                    data.get("motivo"), data.get("suscripcion"), data.get("tipo", "texto"),
                    data.get("archivo_url"), data.get("transcripcion"), updated_at,
                    data.get("is_deleted", 0), note_id
                ))
            else:
                cursor.execute('''
                    INSERT INTO notes (
                        id, ambito, titulo, descripcion, dependencias, ubicacion, enterado, limite,
                        realizada, monto, estado, inicio, fin, frecuencia, abono, restante,
                        motivo, suscripcion, tipo, archivo_url, transcripcion, updated_at, is_deleted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    note_id, data.get("ambito"), data.get("titulo"), data.get("descripcion"),
                    data.get("dependencias"), data.get("ubicacion"), data.get("enterado"),
                    data.get("limite"), data.get("realizada", 0), data.get("monto"),
                    data.get("estado"), data.get("inicio"), data.get("fin"),
                    data.get("frecuencia"), data.get("abono"), data.get("restante"),
                    data.get("motivo"), data.get("suscripcion"), data.get("tipo", "texto"),
                    data.get("archivo_url"), data.get("transcripcion"), updated_at,
                    data.get("is_deleted", 0)
                ))
            conn.commit()

            cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            col_names = [description[0] for description in cursor.description]
            note_dict = dict(zip(col_names, row))
            conn.close()

            self.send_json(note_dict)
            return

        if path in ("/api/sync", "/api/sync/"):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
                client_notes = data.get("notes", [])
            except Exception:
                self.send_json({"error": "Invalid JSON"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            for c_note in client_notes:
                c_id = c_note.get("id")
                c_updated = c_note.get("updated_at") or datetime.utcnow().isoformat()
                
                cursor.execute("SELECT updated_at FROM notes WHERE id = ?", (c_id,))
                row = cursor.fetchone()

                if row:
                    server_updated = row[0] or ""
                    if c_updated >= server_updated:
                        cursor.execute('''
                            UPDATE notes SET
                                ambito = ?, titulo = ?, descripcion = ?, dependencias = ?, ubicacion = ?,
                                enterado = ?, limite = ?, realizada = ?, monto = ?, estado = ?, inicio = ?,
                                fin = ?, frecuencia = ?, abono = ?, restante = ?, motivo = ?, suscripcion = ?,
                                tipo = ?, archivo_url = COALESCE(?, archivo_url), transcripcion = COALESCE(?, transcripcion),
                                updated_at = ?, is_deleted = ?
                            WHERE id = ?
                        ''', (
                            c_note.get("ambito"), c_note.get("titulo"), c_note.get("descripcion"),
                            c_note.get("dependencias"), c_note.get("ubicacion"), c_note.get("enterado"),
                            c_note.get("limite"), c_note.get("realizada", 0), c_note.get("monto"),
                            c_note.get("estado"), c_note.get("inicio"), c_note.get("fin"),
                            c_note.get("frecuencia"), c_note.get("abono"), c_note.get("restante"),
                            c_note.get("motivo"), c_note.get("suscripcion"), c_note.get("tipo", "texto"),
                            c_note.get("archivo_url"), c_note.get("transcripcion"), c_updated,
                            c_note.get("is_deleted", 0), c_id
                        ))
                else:
                    cursor.execute('''
                        INSERT INTO notes (
                            id, ambito, titulo, descripcion, dependencias, ubicacion, enterado, limite,
                            realizada, monto, estado, inicio, fin, frecuencia, abono, restante,
                            motivo, suscripcion, tipo, archivo_url, transcripcion, updated_at, is_deleted
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        c_id, c_note.get("ambito"), c_note.get("titulo"), c_note.get("descripcion"),
                        c_note.get("dependencias"), c_note.get("ubicacion"), c_note.get("enterado"),
                        c_note.get("limite"), c_note.get("realizada", 0), c_note.get("monto"),
                        c_note.get("estado"), c_note.get("inicio"), c_note.get("fin"),
                        c_note.get("frecuencia"), c_note.get("abono"), c_note.get("restante"),
                        c_note.get("motivo"), c_note.get("suscripcion"), c_note.get("tipo", "texto"),
                        c_note.get("archivo_url"), c_note.get("transcripcion"), c_updated,
                        c_note.get("is_deleted", 0)
                    ))
                    if c_note.get("is_deleted", 0) == 0:
                        threading.Thread(
                            target=process_background_notifications,
                            args=(
                                c_note.get("ambito"),
                                c_note.get("titulo"),
                                c_note.get("descripcion"),
                                c_note.get("limite")
                            )
                        ).start()
            conn.commit()

            cursor.execute("SELECT * FROM notes")
            rows = [dict(zip([d[0] for d in cursor.description], r)) for r in cursor.fetchall()]
            conn.close()

            self.send_json({"server_notes": rows, "status": "success"})
            return

        if path == "/api/notes/upload-audio":
            # Simple multipart parser for audio file upload
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            timestamp = int(time.time() * 1000)
            filename = f"audio_{timestamp}.webm"
            filepath = os.path.join(UPLOAD_DIR, filename)

            # Simple extraction of binary data between boundaries or saving body
            # For robustness, we save the raw body or extract file bytes
            try:
                # Basic heuristic to extract file part from multipart form data
                boundary = content_type.split("boundary=")[1].encode()
                parts = body.split(boundary)
                file_bytes = b""
                for part in parts:
                    if b"filename=" in part:
                        header_body = part.split(b"\r\n\r\n", 1)
                        if len(header_body) == 2:
                            file_bytes = header_body[1].rsplit(b"\r\n", 1)[0]
                if not file_bytes:
                    file_bytes = body # Fallback
                
                with open(filepath, "wb") as f:
                    f.write(file_bytes)
            except Exception:
                with open(filepath, "wb") as f:
                    f.write(body)

            self.send_json({
                "file_url": f"/uploads/{filename}",
                "transcription": "Audio grabado correctamente (Nota de voz guardada)."
            })
            return

        self.send_error(404, "Endpoint not found")

    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        if path.startswith("/api/notes/"):
            note_id = path.split("/")[-1]
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE notes SET is_deleted = 1, updated_at = ? WHERE id = ?", (datetime.utcnow().isoformat(), note_id))
            conn.commit()
            conn.close()
            self.send_json({"status": "deleted"})
            return
        self.send_error(404, "Not found")

    def send_json(self, data, status=200):
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def serve_file(self, filepath):
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            ext = os.path.splitext(filepath)[1].lower()
            content_type = "text/plain"
            if ext == ".html":
                content_type = "text/html"
            elif ext == ".js":
                content_type = "application/javascript"
            elif ext == ".css":
                content_type = "text/css"
            elif ext == ".json":
                content_type = "application/json"
            elif ext == ".webm":
                content_type = "audio/webm"
            elif ext == ".mp3":
                content_type = "audio/mpeg"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    start_scheduler()
    with socketserver.TCPServer(("", PORT), WebHAHandler) as httpd:
        print(f"WEB-HA Server running at http://localhost:{PORT}")
        httpd.serve_forever()
