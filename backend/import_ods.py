import os
import zipfile
import xml.etree.ElementTree as ET
import sqlite3
import uuid
from datetime import datetime

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "database.sqlite"))
ODS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../DetallesAmbitos.ods"))

def parse_ods():
    if not os.path.exists(ODS_FILE):
        print(f"Error: {ODS_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    with zipfile.ZipFile(ODS_FILE, 'r') as z:
        with z.open('content.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            for table in root.iter('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table'):
                tname = table.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name')
                rows = list(table.iter('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-row'))
                if len(rows) <= 1:
                    continue

                headers = []
                for r_idx, row in enumerate(rows):
                    row_vals = []
                    for cell in row.iter('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-cell'):
                        rep = int(cell.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated', 1))
                        text_els = list(cell.iter('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'))
                        cell_text = ''.join([''.join(p.itertext()) for p in text_els])
                        for _ in range(rep):
                            row_vals.append(cell_text)

                    if r_idx == 0:
                        headers = row_vals
                        continue

                    if not any(row_vals):
                        continue

                    # Map row data based on sheet name
                    note_id = "ods_" + uuid.uuid4().hex[:10]
                    ambito = tname
                    titulo = row_vals[0] if len(row_vals) > 0 and row_vals[0] else "Sin título"
                    descripcion = row_vals[1] if len(row_vals) > 1 else ""
                    dependencias = row_vals[2] if len(row_vals) > 2 else ""
                    ubicacion = row_vals[3] if len(row_vals) > 3 else ""
                    enterado = row_vals[4] if len(row_vals) > 4 else ""
                    limite = row_vals[5] if len(row_vals) > 5 else ""
                    realizada = 1 if len(row_vals) > 6 and str(row_vals[6]).strip().lower() in ["1", "true", "si", "sí", "realizada"] else 0

                    monto = None
                    estado = None
                    inicio = None
                    fin = None
                    frecuencia = None
                    abono = None
                    restante = None
                    motivo = None
                    suscripcion = None

                    if tname in ["Plataformas", "Servicios"]:
                        suscripcion = row_vals[2] if len(row_vals) > 2 else ""
                        inicio = row_vals[3] if len(row_vals) > 3 else ""
                        fin = row_vals[4] if len(row_vals) > 4 else ""
                        estado = row_vals[5] if len(row_vals) > 5 else ""
                        try:
                            monto = float(row_vals[6]) if len(row_vals) > 6 and row_vals[6] else None
                        except:
                            monto = None
                        ambito = row_vals[7] if len(row_vals) > 7 and row_vals[7] else tname

                    elif tname == "Deudas":
                        inicio = row_vals[2] if len(row_vals) > 2 else ""
                        fin = row_vals[3] if len(row_vals) > 3 else ""
                        try:
                            abono = float(row_vals[4]) if len(row_vals) > 4 and row_vals[4] else None
                        except:
                            abono = None
                        try:
                            restante = float(row_vals[5]) if len(row_vals) > 5 and row_vals[5] else None
                        except:
                            restante = None
                        ambito = row_vals[6] if len(row_vals) > 6 and row_vals[6] else "Deudas"
                        limite = row_vals[7] if len(row_vals) > 7 else ""

                    elif tname == "Constantes":
                        enterado = row_vals[2] if len(row_vals) > 2 else ""
                        limite = row_vals[3] if len(row_vals) > 3 else ""
                        dependencias = row_vals[4] if len(row_vals) > 4 else ""
                        ambito = row_vals[5] if len(row_vals) > 5 and row_vals[5] else "Constantes"
                        motivo = row_vals[6] if len(row_vals) > 6 else ""

                    elif tname == "Avisos":
                        enterado = row_vals[2] if len(row_vals) > 2 else ""
                        limite = row_vals[3] if len(row_vals) > 3 else ""
                        dependencias = row_vals[4] if len(row_vals) > 4 else ""
                        ambito = row_vals[5] if len(row_vals) > 5 and row_vals[5] else "Avisos"

                    # Insert or replace into SQLite
                    cursor.execute('''
                        INSERT OR REPLACE INTO notes (
                            id, ambito, titulo, descripcion, dependencias, ubicacion, enterado, limite,
                            realizada, monto, estado, inicio, fin, frecuencia, abono, restante,
                            motivo, suscripcion, tipo, updated_at, is_deleted
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'texto', ?, 0)
                    ''', (
                        note_id, ambito, titulo, descripcion, dependencias, ubicacion, enterado, limite,
                        realizada, monto, estado, inicio, fin, None, abono, restante,
                        motivo, suscripcion, datetime.utcnow().isoformat()
                    ))
                    print(f"Imported [{ambito}]: {titulo}")

    conn.commit()
    conn.close()
    print("¡Importación de DetallesAmbitos.ods completada con éxito!")

if __name__ == "__main__":
    parse_ods()
