"""Asistencia v2 (tool general): REGLA DE MENTORÍA. A quien HOY tiene grupo y en algún mes figuró en el maestro como `8. Mentores` (mentor sin grupo),
todas las sesiones de esos meses le cuentan como asistidas. Única definición de la regla (explicación y límites: knowledge/flows/asistencia_v2.md).
Es un registro derivado: `asistencias` dice qué debe haber, `incorporar` lo pone en el cálculo y `sincronizar` lo deja escrito en el Fact:
un registro por sábado con `origen` = mentoria y `grupo` = 8. Mentores (ese mes no tenían grupo; en el dashboard cuentan en su grupo actual).
Si el maestro cambia, la versión anterior queda con vigente = 0 y se agrega la nueva; nunca se borra ni se toca lo que envía el formulario.
Uso: python tools/asistencia/asistencia_mentoria.py --fact [id] [--ejecutar]   (sin id: J1_FACT_ASISTENCIA_ID; sin --ejecutar solo muestra el plan)
Lo corre el Action antes de cada actualización del dashboard. Imprime solo conteos.
"""
import argparse
import datetime
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("tools/core", "tools/maestros", "tools/asistencia"):
    sys.path.insert(0, str(ROOT / p))
from asistencia_dni import persona  # noqa: E402
from asistencia_modelo import ORIGEN_MENTORIA  # noqa: E402
from asistencia_motor import calcular  # noqa: E402


# ---- la regla ----
def meses_acreditados(personas, historial, tipo):
    """{dni vigente: {'AAAA-MM'}}: meses en que cada persona que hoy tiene grupo figuró con TIPO_GRUPO = `tipo`. `historial`: {mes: filas del maestro}.
    Se reconoce por DNI y, si el DNI cambió, por nombre y nacimiento (solo si es única). La foto es mensual: vale el tipo con que cerró el mes."""
    activos = [x for x in personas if x.get("GRUPO_ACTUAL")]
    por_dni, por_persona = {str(x["DNI"]) for x in activos}, {}
    for x in activos:
        por_persona.setdefault(persona(x), []).append(str(x["DNI"]))
    en_maestro = {str(x["DNI"]) for x in personas}
    out = {}
    for ym, filas in historial.items():
        for x in filas:
            if (x.get("TIPO_GRUPO") or "").strip() != tipo:
                continue
            dni, iguales = str(x["DNI"]), por_persona.get(persona(x), [])
            if dni in por_dni:
                out.setdefault(dni, set()).add(ym)
            elif dni not in en_maestro and len(iguales) == 1:
                out.setdefault(iguales[0], set()).add(ym)
    return out


def sin_mentoria(registros):
    return [r for r in registros if r.get("origen") != ORIGEN_MENTORIA]


def asistencias(R, alias, personas, registros, asistentes, historial):
    """{sábado: {dni}} que deben contar por mentoría: sesiones válidas del grupo actual de la persona en esos meses, salvo las que ya tienen asistencia real."""
    if not R.tipo_acreditado:
        return {}
    reales = sin_mentoria(registros)
    meses = meses_acreditados(personas, historial, R.tipo_acreditado)
    base = calcular(R, alias, personas, reales, asistentes)
    sabado = {r["registro_id"]: r["sabado"] for r in reales if str(r["vigente"]) == "1"}
    marcadas = {(sabado[a["registro_id"]], str(a["dni"])) for a in asistentes if a["registro_id"] in sabado}
    out = {}
    for p in base["personas"]:
        for d in base["sesiones_validas"][p["grupo_id"]]:
            if d[:7] in meses.get(p["dni"], ()) and (d, p["dni"]) not in marcadas:
                out.setdefault(d, set()).add(p["dni"])
    return out


def incorporar(registros, asistentes, debidas, tipo):
    """(registros, asistentes) con la mentoría al día: lo que hubiera escrito en el Fact se reemplaza por lo que dice hoy la regla."""
    viejas = {r["registro_id"] for r in registros if r.get("origen") == ORIGEN_MENTORIA}
    regs = sin_mentoria(registros) + [{"registro_id": f"M{d}", "sabado": d, "grupo": tipo, "origen": ORIGEN_MENTORIA, "vigente": "1"} for d in debidas]
    return regs, [a for a in asistentes if a["registro_id"] not in viejas] + [{"registro_id": f"M{d}", "dni": x} for d, dnis in debidas.items() for x in sorted(dnis)]


# ---- el registro en el Fact ----
def escritas(registros, asistentes):
    """{sábado: {'dnis', 'version', 'fila'}} de lo que el Fact tiene hoy por mentoría (`fila` = fila de la hoja del registro vigente, o None)."""
    out = {}
    for i, r in enumerate(registros, start=2):
        if r["origen"] == ORIGEN_MENTORIA:
            e = out.setdefault(r["sabado"], {"dnis": set(), "version": 0, "fila": None})
            e["version"] = max(e["version"], int(r["version"]))
            if str(r["vigente"]) == "1":
                e["fila"], e["dnis"] = i, {str(a["dni"]) for a in asistentes if a["registro_id"] == r["registro_id"]}
    return out


def plan(debidas, hay, tipo, ahora):
    """(filas cuyo registro deja de estar vigente, registros nuevos, asistentes nuevos)."""
    bajas, regs, asis = [], [], []
    for d in sorted(set(debidas) | set(hay)):
        quiero, e = debidas.get(d, set()), hay.get(d, {"dnis": set(), "version": 0, "fila": None})
        if quiero == e["dnis"]:
            continue
        if e["fila"]:
            bajas.append(e["fila"])
        if quiero:
            v = e["version"] + 1
            rid = f"M{d.replace('-', '')}-{v}"
            regs.append({"registro_id": rid, "enviado_el": ahora, "fecha_reunion": d, "sabado": d, "grupo": tipo, "origen": ORIGEN_MENTORIA, "fila_form_viejo": "", "version": v, "vigente": 1})
            asis += [{"registro_id": rid, "dni": int(x)} for x in sorted(quiero)]
    return bajas, regs, asis


def main():
    from asistencia_carga import cargar_tablas_drive, calcular_hoy
    from maestros_drive import servicios, reint
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fact", nargs="?", const="", default="")
    ap.add_argument("--ejecutar", action="store_true")
    a = ap.parse_args()
    fact = a.fact or os.environ.get("J1_FACT_ASISTENCIA_ID") or sys.exit("Falta el id del Fact.")
    T = cargar_tablas_drive(fact)
    c = calcular_hoy(T)
    debidas, tipo = c["mentoria"], c["R"].tipo_acreditado
    bajas, regs, asis = plan(debidas, escritas(T["registro"], T["asistente"]), tipo, datetime.datetime.now().isoformat(timespec="seconds"))
    print(f"Mentoría: {len(set().union(*debidas.values())) if debidas else 0} personas, {sum(map(len, debidas.values()))} asistencias en {len(debidas)} sábados"
          f" | por escribir en el Fact: {len(regs)} registros, {len(asis)} asistentes | reemplazados: {len(bajas)}")
    if not (bajas or regs) or not a.ejecutar:
        print("El Fact ya está al día." if not (bajas or regs) else "Plan (no se escribió nada): agrega --ejecutar.")
        return
    sheets = servicios()[1]
    valores = sheets.spreadsheets().values()
    cab = {n: reint(valores.get(spreadsheetId=fact, range=f"'{n}'!1:1"))["values"][0] for n in ("registro", "asistente")}
    for n, filas in (("asistente", asis), ("registro", regs)):  # primero los asistentes: un registro vigente nunca queda sin su gente
        if filas:
            reint(valores.append(spreadsheetId=fact, range=f"'{n}'!A1", valueInputOption="RAW", insertDataOption="INSERT_ROWS", body={"values": [[f.get(k, "") for k in cab[n]] for f in filas]}))
    if bajas:
        col = chr(ord("A") + cab["registro"].index("vigente"))
        reint(valores.batchUpdate(spreadsheetId=fact, body={"valueInputOption": "RAW", "data": [{"range": f"'registro'!{col}{f}", "values": [[0]]} for f in bajas]}))
    T2 = cargar_tablas_drive(fact)
    ok = {d: e["dnis"] for d, e in escritas(T2["registro"], T2["asistente"]).items() if e["dnis"]} == debidas and len(T2["registro"]) == len(T["registro"]) + len(regs)
    print(f"Verificación leyendo de vuelta: {'OK' if ok else 'FALLA'} ({len(T2['registro'])} registros, {len(T2['asistente'])} asistentes)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
