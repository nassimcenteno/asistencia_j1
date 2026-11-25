"""Asistencia v2 (tool general): que una asistencia nunca quede huérfana cuando una persona cambia de DNI en el maestro.
La asistencia se guarda por DNI (el del maestro). Si el DNI de una persona cambia (ficticio -> real, o corregido), sus asistencias viejas apuntarían a un DNI que ya no existe.
Tres capas, sin tabla de apoyo:
  1. ESCRITURA CONJUNTA (`reasignar`): `tools/maestros/editar_maestro.py` cambia también `asistente.dni` del Fact en la misma operación. Cubre toda edición hecha con la tool.
  2. AUTOSANACIÓN (`sanar`): al calcular, un DNI de asistencia que ya no está en el maestro se reconoce por la persona (nombre + fecha de nacimiento) usando los maestros
     de meses anteriores, y se lleva al DNI vigente. Cubre ediciones hechas a mano que no borraron el DNI viejo de todo el historial. Solo actúa si la identidad es única.
  3. ALARMA: lo que ni la autosanación resuelve queda como huérfano y se avisa con conteos (consola y dashboard); nunca se pierde en silencio.
"""
import csv
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("tools/core", "tools/maestros"):
    sys.path.insert(0, str(ROOT / p))
from maestros_formato import norm  # noqa: E402


def persona(x):
    """Identidad estable de una fila del maestro: nombre completo normalizado + fecha de nacimiento."""
    return (norm(x.get("NOM_COMPLETO", "")), str(x.get("FECHA_NACIMIENTO") or "").strip())


def huerfanos(asistentes, dnis_maestro):
    """DNI de asistencia que no están en el maestro vigente."""
    return {str(a["dni"]) for a in asistentes} - dnis_maestro


def sanar(asistentes, personas, historial):
    """(asistentes con el DNI actualizado, {dni_viejo: dni_nuevo}). `personas`: filas del maestro vigente. `historial`: función sin argumentos que devuelve
    {mes: filas} de los maestros (se invoca solo si hay huérfanos). Un DNI viejo se lleva al nuevo únicamente si identifica a UNA persona en el historial
    y esa persona está UNA vez en el maestro vigente; si no, queda huérfano (se avisa)."""
    en_maestro = {str(x["DNI"]) for x in personas}
    sin = huerfanos(asistentes, en_maestro)
    if not sin:
        return asistentes, {}
    vigentes = {}
    for x in personas:
        vigentes.setdefault(persona(x), []).append(str(x["DNI"]))
    quienes = {}  # dni huérfano -> identidades que lo usaron en el pasado
    for filas in historial().values():
        for x in filas:
            if str(x["DNI"]) in sin:
                quienes.setdefault(str(x["DNI"]), set()).add(persona(x))
    mapa = {}
    for viejo, identidades in quienes.items():
        if len(identidades) != 1:
            continue
        actuales = vigentes.get(next(iter(identidades)), [])
        if len(actuales) == 1:
            mapa[viejo] = actuales[0]
    if not mapa:
        return asistentes, {}
    return [{**a, "dni": mapa.get(str(a["dni"]), a["dni"])} for a in asistentes], mapa


# ---- escritura conjunta con el Fact (la usa editar_maestro) ----
def _leer(sheets, fact):
    from maestros_drive import reint
    return reint(sheets.spreadsheets().values().get(spreadsheetId=fact, range="'asistente'!A1:B30000", valueRenderOption="UNFORMATTED_VALUE")).get("values", [])


def contar(sheets, fact, viejo):
    """Cuántas asistencias del Fact tienen ese DNI."""
    v = _leer(sheets, fact)
    c = v[0].index("dni")
    return sum(1 for r in v[1:] if len(r) > c and str(r[c]) == str(viejo))


def reasignar(sheets, fact, pares, respaldo_dir):
    """Cambia en `asistente.dni` cada DNI viejo por el nuevo (pares = [(viejo, nuevo)]). Respalda la pestaña, escribe y verifica leyendo de vuelta.
    Devuelve {viejo: filas cambiadas}. Es idempotente: si ya se cambió, no hay nada que hacer."""
    from maestros_drive import reint
    v = _leer(sheets, fact)
    c = v[0].index("dni")
    mapa = {str(a): str(b) for a, b in pares}
    cambios = [(i + 1, mapa[str(r[c])]) for i, r in enumerate(v[1:], start=1) if len(r) > c and str(r[c]) in mapa]
    hechos = {a: sum(1 for i, r in enumerate(v[1:]) if len(r) > c and str(r[c]) == a) for a in mapa}
    if not cambios:
        return hechos
    respaldo = Path(respaldo_dir) / f"asistente_antes_de_cambiar_dni_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
    respaldo.parent.mkdir(parents=True, exist_ok=True)
    with open(respaldo, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(v)
    col = chr(ord("A") + c)
    reint(sheets.spreadsheets().values().batchUpdate(spreadsheetId=fact, body={"valueInputOption": "RAW", "data": [
        {"range": f"'asistente'!{col}{fila}", "values": [[int(nuevo)]]} for fila, nuevo in cambios]}))
    despues = _leer(sheets, fact)
    quedan = sum(1 for r in despues[1:] if len(r) > c and str(r[c]) in mapa)
    if quedan or len(despues) != len(v):
        raise RuntimeError(f"Verificación fallida al cambiar DNI en el Fact (quedan {quedan}); respaldo: {respaldo}")
    return hechos
