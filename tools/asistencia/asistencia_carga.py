"""Asistencia v2 (tool general): carga las tablas del modelo y calcula "hoy" con el maestro vigente.
Es el punto de entrada de cualquier análisis de asistencia (dashboard, reportes, auditoría): tablas -> reglas y alias -> motor.
Las tablas son CSV con el contrato del Fact (`registro`, `asistente`, `grupos`, ...); cuando el Fact viva en Drive, solo cambia de dónde se leen.
Regla de la semana en curso (parámetro `semana_en_curso_dias`): la última sesión, mientras no pasen más de esos días, queda fuera de
KPI, estados, ranking y riesgo (aún están registrando) y se devuelve aparte como `en_curso`.
Un DNI cambiado en el maestro no deja asistencias huérfanas: ver `asistencia_dni.py`.
"""
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("tools/core", "tools/maestros", "tools/asistencia"):
    sys.path.insert(0, str(ROOT / p))
from maestros_drive import vigente, cargar, cargar_todos, servicios, reint  # noqa: E402
from asistencia_modelo import leer_tabla, Alias  # noqa: E402
from asistencia_reglas import Reglas  # noqa: E402
from asistencia_motor import calcular  # noqa: E402
from asistencia_dni import sanar, huerfanos  # noqa: E402

TABLAS = ("registro", "asistente", "grupos", "calendario", "parametros")


def cargar_tablas(carpeta):
    """{nombre: lista de dicts} desde una carpeta con las tablas .csv."""
    return {n: leer_tabla(Path(carpeta) / f"{n}.csv") for n in TABLAS}


def cargar_tablas_drive(fact_id):
    """Igual que `cargar_tablas`, pero leyendo las pestañas del Fact en Drive (lo que usa el Action). Todo como texto, igual que un CSV."""
    _, sheets = servicios()
    T = {}
    for n in TABLAS:
        v = reint(sheets.spreadsheets().values().get(spreadsheetId=fact_id, range=f"'{n}'!A1:Z30000", valueRenderOption="FORMATTED_VALUE")).get("values", [])
        T[n] = [dict(zip(v[0], r + [""] * (len(v[0]) - len(r)))) for r in v[1:] if any(str(c).strip() for c in r)]
    return T


def reglas_y_alias(T):
    """(Reglas, Alias de grupos) desde las tablas. `asistente.dni` ya es el DNI del maestro."""
    return Reglas(T["grupos"], T["calendario"], T["parametros"]), Alias(T["grupos"])


def calcular_hoy(T, hoy=None):
    """Motor con el maestro vigente (grupos de hoy hacia atrás). Devuelve dict: R, res (sin la semana en curso), full (con ella),
    en_curso (su fila de evolución o None), maestro (mes del maestro usado), sanados (DNI de asistencia llevados al DNI actual de la persona)
    y huerfanos (asistencias cuyo DNI no está en el maestro ni se pudo resolver: no se cuentan y se avisa). Ambos como {dnis, asistencias}."""
    R, alias = reglas_y_alias(T)
    maestro_ym, _ = vigente()
    personas = cargar(maestro_ym)
    original = T["asistente"]
    asistentes, mapa = sanar(original, personas, cargar_todos)
    vigentes = {r["registro_id"] for r in T["registro"] if str(r["vigente"]) == "1"}
    sin_persona = huerfanos(asistentes, {str(x["DNI"]) for x in personas})
    sin = [a for a in asistentes if a["registro_id"] in vigentes and str(a["dni"]) in sin_persona]
    resultado = {"R": R, "maestro": maestro_ym,
                 "sanados": {"dnis": len(mapa), "asistencias": sum(1 for a in original if str(a["dni"]) in mapa)},
                 "huerfanos": {"dnis": len({str(a["dni"]) for a in sin}), "asistencias": len(sin)}}
    full = calcular(R, alias, personas, T["registro"], asistentes)
    fechas = [e["fecha"] for e in full["evolucion"]]
    hoy = hoy or datetime.date.today()
    if R.semana_en_curso_dias and len(fechas) > 1 and (hoy - datetime.date.fromisoformat(fechas[-1])).days <= R.semana_en_curso_dias:
        res = calcular(R, alias, personas, T["registro"], asistentes, hasta=datetime.date.fromisoformat(fechas[-2]))
        return {**resultado, "res": res, "full": full, "en_curso": full["evolucion"][-1]}
    return {**resultado, "res": full, "full": full, "en_curso": None}
