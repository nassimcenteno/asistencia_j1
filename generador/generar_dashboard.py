"""Proyecto 2026-11-18_asistencia_v2 — genera el dashboard (un HTML autocontenido) con el motor de `tools/asistencia`.
Las REGLAS viven solo en Python (asistencia_reglas/asistencia_motor): el HTML recibe datos ya resueltos + `params` y solo suma y divide.
Privacidad: el HTML NO lleva DNI (las personas se identifican por un número interno); sí lleva nombres, como el dashboard actual.
Uso: python projects/2026-11-18_asistencia_v2/tools/generar_dashboard.py (--tablas <carpeta con las tablas .csv> | --fact <id del Fact en Drive>) --salida <index.html>
`--tablas` = outputs/fact_nuevo del proyecto; `--fact` lee las pestañas del Fact en Drive (así corre el Action; sin valor usa J1_FACT_ASISTENCIA_ID).
El maestro es siempre el vigente (el más reciente). Imprime solo conteos (los logs de GitHub Actions pueden ser públicos).
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "asistencia").is_dir())  # raíz del repo (aquí o en el paquete del Action)
sys.path.insert(0, str(ROOT / "tools" / "asistencia"))
from asistencia_carga import cargar_tablas, cargar_tablas_drive, calcular_hoy  # noqa: E402

PLANTILLA = Path(__file__).resolve().parent / "plantillas" / "dashboard.html"
MARCA = "__ASISTENCIA_DATA__"


def compactar(R, res, params_extra, full=None, en_curso=None):
    """Pasa el resultado del motor a un JSON compacto para el HTML (sin DNI; fechas por índice)."""
    fechas = sorted({h["fecha"] for p in res["personas"] for h in p["sesiones"]} | {h["fecha"] for p in res["personas"] for h in p["sesiones_grupo"]})
    ix = {f: i for i, f in enumerate(fechas)}
    ultima_por_dni = {}
    if full is not None and en_curso is not None:
        for p in full["personas"]:
            h = p["sesiones"][-1] if p["sesiones"] else None
            if h and h["fecha"] == en_curso["fecha"]:
                ultima_por_dni[p["dni"]] = int(h["asistio"])
    personas = []
    for n, p in enumerate(res["personas"]):
        personas.append({
            "i": n, "n": p["nombre_completo"], "gid": p["grupo_id"], "g": p["grupo_actual"], "p": p["proyecto"], "t": p["tipo_grupo"], "r": p["rol"],
            "m": int(p["es_miembro"]), "f": p["fecha_ingreso"], "ar": int(p["at_risk"]), "ua": p["ultima_asistencia"], "rc": p["racha_actual"],
            "s": [[ix[h["fecha"]], int(h["asistio"])] for h in p["sesiones"]], "sg": [[ix[h["fecha"]], int(h["asistio"])] for h in p["sesiones_grupo"]],
            "mt": [ix[h["fecha"]] for h in p["sesiones"] if h["acreditada"]],  # sesiones contadas por su periodo como 8. Mentores
            "c": ultima_por_dni.get(p["dni"])})  # asistencia de la semana en curso (None si no le aplica)
    if en_curso is not None and en_curso["fecha"] not in ix:
        fechas.append(en_curso["fecha"])
        ix[en_curso["fecha"]] = len(fechas) - 1
    grupos = [{"gid": g["grupo_id"], "n": g["nombre"], "p": g["proyecto"], "t": g["tipo_grupo"]} for g in res["grupos"]]
    return {
        "generado": res["generated_at"], "fechas": fechas, "q": [R.quarter(datetime.date.fromisoformat(f)) for f in fechas],
        "eventos": {f: e for f, e in res["eventos"].items()}, "personas": personas, "grupos": grupos, "en_curso": en_curso["fecha"] if en_curso else None,
        "params": {"inconstante": R.umbral_inconstante, "activo": R.umbral_activo, "ventana": R.ventana_riesgo, "parcial": R.semana_parcial_max,
                   "quarters": [{"q": q, "ini": i.isoformat(), "fin": f.isoformat() if f else None} for q, i, f in R.quarters], **params_extra}}


def preparar(T, hoy=None):
    """(Reglas, resultado del motor, datos compactos del HTML, resultado de `calcular_hoy`). La semana en curso viaja aparte como asistencia provisional por persona."""
    c = calcular_hoy(T, hoy)
    extra = {"maestro": c["maestro"], "viajeros": c["R"].viajeros, "sin_persona": c["huerfanos"]["asistencias"]}
    return c["R"], c["res"], compactar(c["R"], c["res"], extra, c["full"], c["en_curso"]), c


def escribir(data, salida):
    html = PLANTILLA.read_text(encoding="utf-8")
    if html.count(MARCA) != 1:
        sys.exit(f"La plantilla debe contener {MARCA} exactamente una vez")
    out = Path(salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html.replace(MARCA, json.dumps(data, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split(chr(10))[0])
    origen = ap.add_mutually_exclusive_group()
    origen.add_argument("--tablas", help="carpeta con las tablas .csv")
    origen.add_argument("--fact", nargs="?", const="", help="id del Fact en Drive (sin valor: J1_FACT_ASISTENCIA_ID)")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    if a.tablas:
        T = cargar_tablas(a.tablas)
    else:
        fact = a.fact or os.environ.get("J1_FACT_ASISTENCIA_ID")
        if not fact:
            sys.exit("Indica --tablas <carpeta> o --fact <id> (o J1_FACT_ASISTENCIA_ID).")
        T = cargar_tablas_drive(fact)
    R, res, data, c = preparar(T)
    out = escribir(data, a.salida)
    print(f"[OK] {out} | personas {len(data['personas'])} | grupos {len(data['grupos'])} | sesiones {len(data['fechas'])} | maestro {data['params']['maestro']} | {out.stat().st_size // 1024} KB")
    print(f"[INFO] mentoría: {len(c['acreditados'])} personas con meses en '{c['R'].tipo_acreditado}' dentro del ciclo")
    if c["sanados"]["dnis"]:
        print(f"[INFO] {c['sanados']['asistencias']} asistencias de {c['sanados']['dnis']} DNI cambiados en el maestro se llevaron al DNI actual de la persona")
    if c["huerfanos"]["asistencias"]:
        print(f"[AVISO] {c['huerfanos']['asistencias']} asistencias de {c['huerfanos']['dnis']} DNI no están en el maestro y no se pudieron resolver: no se cuentan")


if __name__ == "__main__":
    main()
