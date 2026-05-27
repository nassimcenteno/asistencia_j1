"""
Setup Google OAuth 2.0 - correr UNA sola vez antes de usar el proyecto.
Requiere credentials.json en la raiz del proyecto.
Genera token.json al completar la autorizacion.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

def main():
    print("=" * 60)
    print("  SETUP: Autenticacion Google OAuth 2.0")
    print("=" * 60)

    credentials_path = ROOT / "config" / "credentials.json"
    token_path = ROOT / "config" / "token.json"
    env_path = ROOT / ".env"

    # --- Verificar credentials.json ---
    if not credentials_path.exists():
        print("\n[ERROR] No se encontro credentials.json en:", ROOT)
        print("\nPasos para obtenerlo:")
        print("  1. Ve a https://console.cloud.google.com/")
        print("  2. Crea un proyecto (o usa uno existente)")
        print("  3. Menu lateral -> APIs y servicios -> Biblioteca")
        print("     Busca 'Google Sheets API' y habilitala")
        print("  4. Menu lateral -> APIs y servicios -> Credenciales")
        print("  5. Crear credenciales -> ID de cliente OAuth 2.0")
        print("     Tipo de aplicacion: Aplicacion de escritorio")
        print("  6. Descarga el JSON -> renombralo a 'credentials.json'")
        print("  7. Colocalo en:", ROOT)
        print("\nLuego vuelve a ejecutar este script.")
        sys.exit(1)

    print("\n[OK] credentials.json encontrado.")

    # --- Verificar dependencias ---
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        import gspread
    except ImportError:
        print("\n[ERROR] Dependencias faltantes. Ejecuta:")
        print("    pip install -r requirements.txt")
        sys.exit(1)

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    # --- Autenticar ---
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\n[...] Refrescando token existente...")
            creds.refresh(Request())
        else:
            print("\n[...] Abriendo el browser para autorizar acceso a Google Sheets...")
            print("      Selecciona tu cuenta de Google y permite el acceso.")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())
        print("\n[OK] token.json generado correctamente.")

    # --- Verificar acceso al Sheet ---
    from dotenv import load_dotenv
    load_dotenv(env_path)
    sheet_id = os.getenv("SHEET_ID", "").strip()
    sheet_name = os.getenv("SHEET_NAME", "").strip()

    if not sheet_id:
        print("\n[AVISO] SHEET_ID no configurado en .env")
        print("        Agrega: SHEET_ID=<id del spreadsheet>")
        print("\nAutenticacion OK. Configura .env y vuelve a ejecutar para verificar acceso.")
        sys.exit(0)

    print(f"\n[...] Verificando acceso al Sheet: {sheet_id}")
    try:
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        sheets = [ws.title for ws in spreadsheet.worksheets()]
        print(f"[OK] Acceso OK. Pestanas disponibles: {sheets}")

        if sheet_name and sheet_name not in sheets:
            print(f"\n[AVISO] SHEET_NAME='{sheet_name}' no coincide con ninguna pestana.")
            print(f"        Nombres disponibles: {sheets}")
        elif sheet_name:
            print(f"[OK] Pestana '{sheet_name}' encontrada.")
        else:
            print(f"\n[AVISO] SHEET_NAME esta vacio en .env.")
            print(f"        Opciones disponibles: {sheets}")

    except Exception as e:
        print(f"\n[ERROR] No se pudo acceder al Sheet: {e}")
        print("        Verifica que el SHEET_ID es correcto y que tu cuenta tiene acceso.")
        sys.exit(1)

    print("\n[OK] Setup completo. Ya puedes ejecutar: python tools/run_report.py")


if __name__ == "__main__":
    main()
