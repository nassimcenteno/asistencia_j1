"""Autenticación del Action: cuenta de servicio de solo lectura (secreto GOOGLE_CREDENTIALS). Reemplaza al OAuth interactivo del repo de trabajo."""
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_services():
    """(drive, sheets, None), con la misma forma que el módulo del repo de trabajo."""
    info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False), build("sheets", "v4", credentials=creds, cache_discovery=False), None
