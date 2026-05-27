"""
Tool: fetch_sheets_data.py
Lee la Google Sheet de asistencia y guarda los datos crudos en .tmp/asistencia_raw.json

Autenticacion:
  - En GitHub Actions: variable de entorno GOOGLE_CREDENTIALS con el JSON de la Service Account
  - Local: archivo service_account.json en la raiz del proyecto
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_gspread_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("[ERROR]  Dependencias faltantes. Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

    creds_env = os.getenv("GOOGLE_CREDENTIALS")
    if creds_env:
        info = json.loads(creds_env)
    else:
        sa_path = ROOT / "service_account.json"
        if not sa_path.exists():
            print("[ERROR]  No se encontro service_account.json ni la variable GOOGLE_CREDENTIALS.")
            print("         Coloca el archivo service_account.json en la raiz del proyecto.")
            sys.exit(1)
        with open(sa_path, encoding="utf-8") as f:
            info = json.load(f)

    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


def main():
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[ERROR]  Dependencias faltantes. Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

    load_dotenv(ROOT / ".env")

    sheet_id = os.getenv("SHEET_ID", "").strip()
    sheet_name = os.getenv("SHEET_NAME", "").strip()

    if not sheet_id:
        print("[ERROR]  SHEET_ID no configurado en .env")
        sys.exit(1)
    if not sheet_name:
        print("[ERROR]  SHEET_NAME no configurado en .env (nombre exacto de la pestana)")
        sys.exit(1)

    # --- Autenticar ---
    print("[...]  Conectando a Google Sheets...")
    client = get_gspread_client()

    try:
        spreadsheet = client.open_by_key(sheet_id)
    except Exception as e:
        print(f"[ERROR]  No se pudo abrir el spreadsheet: {e}")
        sys.exit(1)

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except Exception:
        available = [ws.title for ws in spreadsheet.worksheets()]
        print(f"[ERROR]  Pestaña '{sheet_name}' no encontrada.")
        print(f"    Disponibles: {available}")
        sys.exit(1)

    print(f"[...]  Leyendo datos de '{sheet_name}'...")
    records = worksheet.get_all_records(default_blank="")

    if not records:
        print("[AVISO]   La hoja está vacía o no tiene filas con datos.")
        sys.exit(1)

    # --- Guardar raw ---
    TMP_DIR.mkdir(exist_ok=True)
    output_path = TMP_DIR / "asistencia_raw.json"

    payload = {
        "fetched_at": datetime.now().isoformat(),
        "sheet_id": sheet_id,
        "sheet_name": sheet_name,
        "columns": list(records[0].keys()) if records else [],
        "rows": len(records),
        "data": records,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK]  {len(records)} filas guardadas en .tmp/asistencia_raw.json")
    print(f"    Columnas detectadas: {list(records[0].keys())}")


if __name__ == "__main__":
    main()
