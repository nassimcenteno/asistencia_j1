"""Proyecto 2026-11-11_maestros_mensuales
Acceso a los maestros mensuales en Drive (LA FUENTE DE VERDAD) y utilidades comunes de las tools del proyecto.
La base maestra que manda es SIEMPRE el Maestro_J1_AAAA-MM más reciente de la carpeta `01. Maestros_Históricos`.

Uso como módulo (para cualquier análisis):
    import sys; sys.path.insert(0, "tools/maestros")
    from maestros_drive import meses, vigente, cargar, cargar_todos
    meses()            # {'2024-12': id, ..., '2026-11': id}
    vigente()          # ('2026-11', id): el más reciente, el que manda
    cargar('2025-03')  # lista de dicts con las 28 columnas: fechas como date, DNI numérico, vacíos = None
    cargar_todos()     # {mes: filas}
Los meses cerrados se guardan en una caché local desechable (.tmp/maestros_cache) que se invalida sola si el archivo cambia en Drive; el vigente se lee siempre fresco.
Uso por consola:   python tools/maestros/maestros_drive.py [--mes AAAA-MM]   -> resumen (filas, activos, mentores)
Los datos contienen información personal: no copiarlos a otros lugares ni compartirlos.
"""
import sys, re, json, io, time, datetime, argparse, ssl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"  # registro y respaldos locales (ignorados por git)
sys.path.insert(0, str(ROOT / "tools" / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gdrive_auth import get_services  # noqa: E402
from _guard import assert_in_scope  # noqa: E402
from maestros_formato import FORMULAS, FECHAS  # noqa: E402,F401
from googleapiclient.errors import HttpError  # noqa: E402
from googleapiclient.http import MediaIoBaseDownload  # noqa: E402

CARPETA = "1vBtHsYDiIlxuBEZjeMei0ky9QG1whiPt"  # 01. Maestros_Históricos
DIM_ACTUAL = "1PN8ABgIDTrv64QcPnjGov2aLwaF2ITZuR6c480l1T-s"  # legado: solo lectura, nunca se modifica ni se ordena
HOJA = "01. BD_Maestro_J1"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SHEET = "application/vnd.google-apps.spreadsheet"
PAT = re.compile(r"^Maestro_J1_(\d{4}-\d{2})$")
CACHE = ROOT / ".tmp" / "maestros_cache"


def reint(req, intentos=6):
    """Ejecuta una llamada a la API reintentando si Google limita por minuto (429), falla temporalmente (500/503) o se corta la red."""
    for i in range(intentos):
        try:
            return req.execute()
        except HttpError as e:
            if e.resp.status in (429, 500, 503) and i < intentos - 1:
                time.sleep(15 * (i + 1))
                continue
            raise
        except (TimeoutError, ConnectionError, ssl.SSLError) as e:   # cortes de red transitorios (lectura agotada, conexión reiniciada)
            if i < intentos - 1:
                time.sleep(5 * (i + 1))
                continue
            raise


def servicios():
    drive, sheets, _ = get_services()
    assert_in_scope(drive, CARPETA)
    assert CARPETA != DIM_ACTUAL
    return drive, sheets


def listar_todos(drive):
    """{nombre de archivo: id} de la carpeta de maestros."""
    r = drive.files().list(q=f"'{CARPETA}' in parents and trashed=false and mimeType='{SHEET}'", fields="files(id,name)",
                           supportsAllDrives=True, pageSize=200).execute()["files"]
    return {x["name"]: x["id"] for x in r}


def meses(drive=None):
    """{AAAA-MM: id} ordenado; el último es el vigente (el que manda)."""
    drive = drive or servicios()[0]
    return {PAT.match(n).group(1): i for n, i in sorted(listar_todos(drive).items()) if PAT.match(n)}


def vigente(drive=None):
    m = meses(drive)
    ym = max(m)
    return ym, m[ym]


def col_letra(i):
    from openpyxl.utils import get_column_letter
    return get_column_letter(i + 1)


def leer_hoja(sheets, sid):
    """(encabezado, filas) con los valores crudos de Sheets: fechas como número de serie, vacíos = ''."""
    v = reint(sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{HOJA}'!A1:AC5000", valueRenderOption="UNFORMATTED_VALUE")).get("values", [])
    header = [str(x) for x in v[0]]
    rows = [dict(zip(header, [(r[i] if i < len(r) else "") for i in range(len(header))])) for r in v[1:] if any(str(x).strip() for x in r)]
    return header, rows


def tiene_formulas(sheets, sid, header):
    j = header.index("EDAD")
    f = reint(sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{HOJA}'!{col_letra(j)}2:{col_letra(j)}2", valueRenderOption="FORMULA")).get("values", [[""]])
    return bool(f and f[0] and str(f[0][0]).startswith("="))


def escribir_columnas(sheets, sid, header, rows, omitir=()):
    """Reescribe los valores de las filas de datos (valores crudos, sin interpretar). `omitir`: columnas con fórmulas que no se tocan."""
    n = len(rows)
    data = [{"range": f"'{HOJA}'!{col_letra(j)}2:{col_letra(j)}{n + 1}", "values": [["" if r.get(c) is None else r.get(c)] for r in rows]}
            for j, c in enumerate(header) if c not in omitir]
    reint(sheets.spreadsheets().values().batchUpdate(spreadsheetId=sid, body={"valueInputOption": "RAW", "data": data}))


def formulas_intactas(sheets, sid, header, n):
    """True si EDAD, CATEGORIA_EDAD y CATEGORIA son fórmulas en las n filas de datos (maestro vigente)."""
    for c in FORMULAS:
        j = header.index(c)
        f = reint(sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{HOJA}'!{col_letra(j)}2:{col_letra(j)}{n + 1}",
                                                     valueRenderOption="FORMULA")).get("values", [])
        if len(f) != n or not all(x and str(x[0]).startswith("=") for x in f):
            return False
    return True


def asegurar_filas(sheets, sid, n_datos):
    """Hace que la hoja tenga al menos n_datos filas de datos (+ encabezado); agrega las que falten al final."""
    grid = reint(sheets.spreadsheets().get(spreadsheetId=sid, fields="sheets(properties(sheetId,gridProperties))"))["sheets"][0]["properties"]
    faltan = n_datos + 1 - grid["gridProperties"]["rowCount"]
    if faltan > 0:
        reint(sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [
            {"appendDimension": {"sheetId": grid["sheetId"], "dimension": "ROWS", "length": faltan}}]}))


def escribir_formulas(sheets, sid, fila, formulas):
    """Escribe fórmulas (A1, interpretadas) en una fila de datos. formulas: {columna_indice: texto}."""
    data = [{"range": f"'{HOJA}'!{col_letra(j)}{fila}", "values": [[f]]} for j, f in formulas.items()]
    reint(sheets.spreadsheets().values().batchUpdate(spreadsheetId=sid, body={"valueInputOption": "USER_ENTERED", "data": data}))


def exportar_xlsx(drive, sid, destino):
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, drive.files().export_media(fileId=sid, mimeType=XLSX))
    hecho = False
    while not hecho:
        _, hecho = dl.next_chunk()
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(buf.getvalue())


def _convertir(header, filas_crudas):
    base = datetime.date(1899, 12, 30)
    rows = []
    for r in filas_crudas:
        d = {}
        for h in header:
            v = r.get(h, "")
            if v == "":
                v = None
            elif h in FECHAS and isinstance(v, (int, float)):
                v = base + datetime.timedelta(days=int(v))
            elif h in ("DNI", "TELEFONO") and isinstance(v, float) and v.is_integer():
                v = int(v)
            d[h] = v
        rows.append(d)
    return rows


def cargar(ym, fresco=False):
    """Filas de un mes como lista de dicts. Los meses cerrados usan caché desechable; el vigente (el más reciente) se lee siempre de Drive."""
    drive, sheets = servicios()
    m = meses(drive)
    if ym not in m:
        raise KeyError(f"No existe Maestro_J1_{ym} en Drive. Meses: {min(m)} a {max(m)}")
    arch = CACHE / f"{ym}.json"
    cerrado = ym != max(m)
    modificado = reint(drive.files().get(fileId=m[ym], fields="modifiedTime", supportsAllDrives=True))["modifiedTime"] if cerrado else None
    if cerrado and not fresco and arch.exists():
        j = json.loads(arch.read_text(encoding="utf-8"))
        if j.get("modificado") == modificado:  # la caché solo vale si el archivo no cambió en Drive (hay ediciones retroactivas)
            return _convertir(j["header"], j["rows"])
    header, rows = leer_hoja(sheets, m[ym])
    if cerrado:
        CACHE.mkdir(parents=True, exist_ok=True)
        arch.write_text(json.dumps({"modificado": modificado, "header": header, "rows": rows}, ensure_ascii=False), encoding="utf-8")
    return _convertir(header, rows)


def cargar_todos(fresco=False):
    return {ym: cargar(ym, fresco) for ym in meses()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mes", help="mes a resumir (por defecto, el vigente)")
    a = ap.parse_args()
    ym = a.mes or vigente()[0]
    filas = cargar(ym)
    activos = {"1. GBU", "2. GDA", "3. GDC", "8. Mentores", "9. Pastor"}
    print(f"Maestro_J1_{ym}{' (vigente: el que manda)' if ym == vigente()[0] else ''}: {len(filas)} filas | "
          f"activos {sum(1 for r in filas if r['TIPO_GRUPO'] in activos)} | con grupo {sum(1 for r in filas if r['GRUPO_ACTUAL'])} | "
          f"mentores {sum(1 for r in filas if r['ROL_ACTUAL'] == 'Mentor')}")


if __name__ == "__main__":
    main()
