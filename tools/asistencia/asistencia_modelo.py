"""Asistencia v2 (tool general): reglas puras del modelo de datos del Fact_Asistencia (sin Drive).
Fechas (sesión = sábado de la semana, igual que la fórmula histórica), tablas del modelo y resolución de alias de grupo y de persona.
Las tablas (`grupos`, `calendario`, `parametros`, ...) hoy se leen de CSV; después serán pestañas del Fact (mismo contrato: lista de dicts).
Contiene datos personales solo en los archivos que lee (alias_persona, solo del proyecto de migración); este módulo no guarda ninguno.
"""
import csv
import datetime
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "maestros"))
from maestros_formato import norm  # noqa: E402

EPOCA_SHEETS = datetime.date(1899, 12, 30)


def serial_a_fecha(n):
    """Serial de Sheets (entero o con hora) -> date."""
    return EPOCA_SHEETS + datetime.timedelta(days=int(n))


def serial_a_datetime(n):
    return datetime.datetime.combine(EPOCA_SHEETS, datetime.time()) + datetime.timedelta(days=float(n))


def sabado_de(fecha):
    """Sábado de la semana de `fecha` (lun-sáb a su sábado; el domingo cae en el sábado anterior): B + (6 - WEEKDAY(B, 2))."""
    return fecha + datetime.timedelta(days=6 - fecha.isoweekday())


def lista(texto):
    """'a, b, c' -> ['a', 'b', 'c'] (celdas con varios valores separados por coma)."""
    return [x.strip() for x in str(texto or "").split(",") if x.strip()]


def id_grupo(nombre):
    """Código interno de un grupo, derivado de su nombre (nadie lo escribe a mano): 'GDC BETTA VIAJEROS' -> 'gdc_betta_viajeros'."""
    return re.sub(r"[^a-z0-9]+", "_", norm(nombre)).strip("_")


def leer_tabla(ruta):
    """Tabla CSV -> lista de dicts (UTF-8, con o sin BOM)."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def escribir_tabla(ruta, filas, columnas):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)


class Alias:
    """Resolución: nombre de grupo (actual o antiguo, de la tabla grupos) -> grupo_id, y (DNI, nombre) del registro viejo -> DNI del maestro."""

    def __init__(self, grupos, alias_persona=()):
        self.grupos = {}   # nombre (actual o anterior, normalizado) -> grupo_id
        self.nombres = {}  # grupo_id -> nombre actual
        for g in grupos:
            gid = id_grupo(g["grupo"])
            self.nombres[gid] = g["grupo"]
            for nombre in [g["grupo"], *lista(g["antes_se_llamaba"])]:
                self.grupos[norm(nombre)] = gid
        self.personas = {(str(a["dni_registro"]).strip(), norm(a["nombre_registro"])): str(a["dni_maestro"]).strip() for a in alias_persona}

    def grupo(self, nombre):
        """grupo_id o None si el nombre no está en la tabla (el auditor lo reporta)."""
        return self.grupos.get(norm(nombre))

    def dni(self, dni, nombre):
        """DNI vigente: el alias por (dni, nombre) si existe; si no, el mismo DNI."""
        return self.personas.get((str(dni).strip(), norm(nombre)), str(dni).strip())
