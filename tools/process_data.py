"""
Tool: process_data.py
Aplica las reglas de negocio y genera .tmp/asistencia_processed.json
listo para ser consumido por generate_dashboard.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict, Counter

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"

# ---------------------------------------------------------------------------
# Reglas de negocio
# ---------------------------------------------------------------------------

EXCEPTIONS = {
    # 11/4: solo GDC BETTA, GDC BETTA VIAJEROS y GDC SIGMA tuvieron sesion
    "2026-04-11": {"todos_menos": ["GDC BETTA", "GDC BETTA VIAJEROS", "GDC SIGMA"]},
    # 4/7: GDC LAMBDA y GDC SIGMA no tuvieron sesion (por acuerdo)
    "2026-07-04": {"excluir": ["GDC LAMBDA", "GDC SIGMA"]},
    # 3/10: solo GDC BETTA VIAJEROS tuvo sesion
    "2026-10-03": {"todos_menos": ["GDC BETTA VIAJEROS"]},
}

# Proyecto Betta: estos grupos forman el "Proyecto Betta"; todo el resto es J1.
# Se usa solo para el toggle del dashboard (no afecta ningun calculo de asistencia).
PROYECTO_BETTA_GROUPS = {"GDC BETTA", "GDA GAMMA", "GDC BETTA VIAJEROS", "GDC OMEGA"}


def get_proyecto(group_name: str) -> str:
    return "betta" if group_name.strip().upper() in PROYECTO_BETTA_GROUPS else "j1"

# Grupos donde la asistencia manda: en una fecha con 0 asistentes se asume que NO hubo
# sesion esa semana (se excluye del denominador y del conteo de sesiones del grupo);
# si hubo al menos 1 asistente, la sesion cuenta. Es dinamico y retroactivo: reemplaza
# tanto el hold como las excepciones manuales por fecha que antes llevaban estos grupos.
ATTENDANCE_DRIVEN_GROUPS = {"GDC BETTA", "GDC BETTA VIAJEROS"}

EVENTS = {
    "2026-02-28": "JADAK",
    "2026-03-14": "Montecamp",
    "2026-03-21": "Reencuentro Montecamp",
    "2026-05-02": "Apologética",
    "2026-05-16": "El Viaje",
    "2026-06-20": "Puentes",
    "2026-07-11": "EJEC",
    "2026-07-18": "Reencuentro EJEC",
    "2026-08-15": "J-Fest",
    "2026-09-05": "Alaba",
}

GROUP_TYPES = {
    "GBU": "Grupos Universitarios",
    "GDA": "Grupos de Amistad",
    "GDC": "Grupos de Crecimiento",
}

# Grupos creados en el ciclo: sesiones cuentan desde su fecha de creación (inclusive).
GROUP_START_DATES: dict[str, date] = {
    "GDC LAMBDA": date(2026, 5, 16),
    "GDC OMEGA": date(2026, 5, 16),
}

QUARTERS = ["Q1", "Q2", "Q3"]

# Las sesiones de una persona / grupo cuentan desde su fecha de inicio (inclusive).
# FECHA_INGRESO y GROUP_START_DATES se usan tal cual, sin desplazamiento.


def get_quarter(d: date) -> str:
    """Q1: ene-mar | Q2: abr-jul | Q3: ago en adelante."""
    if d.month <= 3:
        return "Q1"
    if d.month <= 7:
        return "Q2"
    return "Q3"


def parse_date(val) -> date | None:
    if not val:
        return None
    val = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def get_status(pct: float) -> str:
    if pct == 0:
        return "Inactivo"
    elif pct <= 40:
        return "Inconstante"
    elif pct <= 74:
        return "Activo"
    else:
        return "Fiel"


def session_applies_to_group(session_date: date, group_name: str) -> bool:
    iso = session_date.isoformat()
    group_upper = group_name.strip().upper()
    if iso in EXCEPTIONS:
        rule = EXCEPTIONS[iso]
        if "todos_menos" in rule:
            return group_upper in [g.upper() for g in rule["todos_menos"]]
        if "excluir" in rule:
            return group_upper not in [g.upper() for g in rule["excluir"]]
    return True


def build_historial(fechas: list[date], fechas_asistidas: set[str]) -> list[dict]:
    out = []
    for d in fechas:
        iso = d.isoformat()
        out.append({
            "fecha": iso,
            "asistio": iso in fechas_asistidas,
            "quarter": get_quarter(d),
            "evento": EVENTS.get(iso),
        })
    return out


def main():
    raw_path = TMP_DIR / "asistencia_raw.json"
    if not raw_path.exists():
        print("[ERROR] .tmp/asistencia_raw.json no encontrado. Ejecuta primero fetch_sheets_data.py")
        sys.exit(1)

    with open(raw_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    rows = raw["data"]
    fetched_at = raw.get("fetched_at", "")
    columns = raw.get("columns", [])

    print(f"[...] Procesando {len(rows)} filas...")

    # ---------------------------------------------------------------------------
    # Detectar columnas
    # ---------------------------------------------------------------------------
    col_map = {}
    for col in columns:
        cl = col.lower().strip()
        if "grupo_actual" in cl or "grupo actual" in cl:
            col_map["grupo_actual"] = col
        elif cl in ("nom_completo", "nombre_completo"):
            col_map["nombre"] = col
        elif "nombre" in cl and "grupo" not in cl and "nom_completo" not in cl:
            col_map.setdefault("nombre", col)
        elif "rol" in cl:
            col_map["rol"] = col
        elif "tipo_miembro" in cl or "tipo miembro" in cl:
            col_map["tipo_miembro"] = col
        elif "tipo_grupo" in cl or "tipo grupo" in cl:
            col_map["tipo_grupo"] = col
        elif "fecha" in cl and ("std" in cl or "reunion" in cl):
            col_map["fecha"] = col
        elif cl == "asistencia":
            col_map["asistencia"] = col
        elif "fecha_ingreso" in cl or "fecha ingreso" in cl or cl == "ingreso":
            col_map["fecha_ingreso"] = col
        elif cl == "dni":
            col_map["dni"] = col

    required = ["nombre", "grupo_actual", "fecha"]
    missing = [k for k in required if k not in col_map]
    if missing:
        print(f"[ERROR] Columnas requeridas no encontradas: {missing}")
        print(f"    Disponibles: {columns}")
        sys.exit(1)

    print(f"    Mapeo: {col_map}")

    # ---------------------------------------------------------------------------
    # Construir estructura por persona
    # ---------------------------------------------------------------------------
    personas: dict = {}
    all_sessions: set[date] = set()
    # (grupo_upper, fecha_iso) -> nro de asistentes de ese grupo esa fecha.
    group_attendance: dict[tuple[str, str], int] = defaultdict(int)

    for row in rows:
        grupo_actual = str(row.get(col_map["grupo_actual"], "")).strip()
        if not grupo_actual:
            continue

        full_name = str(row.get(col_map["nombre"], "")).strip()
        if not full_name:
            continue

        fecha_raw = row.get(col_map["fecha"], "")
        session_date = parse_date(fecha_raw)
        if not session_date:
            continue

        if "asistencia" in col_map:
            val = str(row.get(col_map["asistencia"], "")).strip().upper()
            asistio = val in ("1", "SI", "SÍ", "S", "TRUE", "YES", "X")
        else:
            asistio = True

        all_sessions.add(session_date)
        if asistio:
            group_attendance[(grupo_actual.strip().upper(), session_date.isoformat())] += 1

        dni = str(row.get(col_map.get("dni", ""), "")).strip()
        persona_key = f"{full_name.lower()}|{dni}" if dni else full_name.lower()
        if persona_key not in personas:
            tipo_grupo_raw = str(row.get(col_map.get("tipo_grupo", ""), "")).strip()
            for key in ("GBU", "GDA", "GDC"):
                if key in tipo_grupo_raw.upper():
                    tipo_grupo_raw = key
                    break
            tipo_miembro = str(row.get(col_map.get("tipo_miembro", ""), "")).strip()
            fi_raw = str(row.get(col_map.get("fecha_ingreso", ""), "")).strip()
            fi_date = parse_date(fi_raw)
            personas[persona_key] = {
                "id": persona_key,
                "nombre_completo": full_name,
                "grupo_actual": grupo_actual,
                "rol": str(row.get(col_map.get("rol", ""), "")).strip(),
                "tipo_miembro": tipo_miembro,
                "es_miembro": tipo_miembro in ("Miembro Bautizado", "Transferido"),
                "tipo_grupo": tipo_grupo_raw,
                "fecha_ingreso": fi_date.isoformat() if fi_date else None,
                "active_from": fi_date,
                "sesiones_raw": [],
            }

        personas[persona_key]["sesiones_raw"].append({
            "fecha": session_date.isoformat(),
            "quarter": get_quarter(session_date),
            "evento": EVENTS.get(session_date.isoformat()),
            "asistio": asistio,
        })

    # ---------------------------------------------------------------------------
    # Validez de cada sesion por grupo (necesita el mapa de asistencia completo)
    # ---------------------------------------------------------------------------
    def group_had_session(group_name: str, session_date: date) -> bool:
        """Para grupos en ATTENDANCE_DRIVEN_GROUPS: hubo sesion solo si asistio >= 1 esa fecha."""
        gu = group_name.strip().upper()
        if gu in ATTENDANCE_DRIVEN_GROUPS:
            return group_attendance.get((gu, session_date.isoformat()), 0) > 0
        return True

    def session_valid_for_group(session_date: date, group_name: str) -> bool:
        return (session_applies_to_group(session_date, group_name)
                and group_had_session(group_name, session_date))

    # Marcar aplica_denominador / aplica_grupo en cada sesion de cada persona.
    for p in personas.values():
        grupo = p["grupo_actual"]
        personal_af = p.get("active_from")
        g_af = GROUP_START_DATES.get(grupo.upper())
        effective_af_grupo = max(personal_af, g_af) if personal_af and g_af else (personal_af or g_af)
        for s in p["sesiones_raw"]:
            sd = date.fromisoformat(s["fecha"])
            valida = session_valid_for_group(sd, grupo)
            # Nivel persona: independiente de GROUP_START_DATES, solo su propia FECHA_INGRESO.
            s["aplica_denominador"] = valida and (personal_af is None or sd >= personal_af)
            # Nivel grupo: respeta ademas la fecha de inicio del grupo (GROUP_START_DATES).
            s["aplica_grupo"] = valida and (effective_af_grupo is None or sd >= effective_af_grupo)

    # ---------------------------------------------------------------------------
    # Denominadores por grupo
    # ---------------------------------------------------------------------------
    grupos_set = {p["grupo_actual"] for p in personas.values()}
    # Nivel persona: no aplica GROUP_START_DATES (independiente del grupo).
    sesiones_por_grupo_persona: dict[str, list[date]] = {
        g: sorted(s for s in all_sessions if session_valid_for_group(s, g))
        for g in grupos_set
    }
    # Nivel grupo: si aplica GROUP_START_DATES (reglas propias del grupo).
    sesiones_por_grupo: dict[str, list[date]] = {
        g: sorted(
            s for s in sesiones_por_grupo_persona[g]
            if g.upper() not in GROUP_START_DATES or s >= GROUP_START_DATES[g.upper()]
        )
        for g in grupos_set
    }

    # ---------------------------------------------------------------------------
    # Calcular estadisticas por persona
    # ---------------------------------------------------------------------------
    personas_list = []

    for p in personas.values():
        grupo = p["grupo_actual"]
        sesiones_raw = p["sesiones_raw"]
        active_from = p.get("active_from")
        fechas_aplican = [
            d for d in sesiones_por_grupo_persona.get(grupo, [])
            if active_from is None or d >= active_from
        ]
        fechas_grupo = [
            d for d in sesiones_por_grupo.get(grupo, [])
            if active_from is None or d >= active_from
        ]
        fechas_asistidas = {s["fecha"] for s in sesiones_raw if s["asistio"]}

        # Numerador (nivel persona): un solo paso sobre sesiones_raw.
        asist_q = {q: 0 for q in QUARTERS}
        total_asistencias = 0
        for s in sesiones_raw:
            if s["aplica_denominador"] and s["asistio"]:
                total_asistencias += 1
                asist_q[s["quarter"]] += 1

        total_sesiones = len(fechas_aplican)
        total_q = {q: 0 for q in QUARTERS}
        for d in fechas_aplican:
            total_q[get_quarter(d)] += 1

        pct_total = round(total_asistencias / total_sesiones * 100, 1) if total_sesiones > 0 else 0
        pct_q = {
            q: round(asist_q[q] / total_q[q] * 100, 1) if total_q[q] > 0 else 0
            for q in QUARTERS
        }

        status = get_status(pct_total)
        status_q = {q: get_status(pct_q[q]) if total_q[q] > 0 else None for q in QUARTERS}

        # Nivel persona (sin GROUP_START_DATES) y nivel grupo (con GROUP_START_DATES, usado en drilldown de grupo).
        historial = build_historial(fechas_aplican, fechas_asistidas)
        historial_grupo = build_historial(fechas_grupo, fechas_asistidas)

        # En riesgo: 0 asistencias en las ultimas 4 sesiones que aplican al grupo (dinamico)
        last4_fechas = {h["fecha"] for h in historial[-4:]}
        at_risk = len(last4_fechas) > 0 and not any(h["asistio"] for h in historial if h["fecha"] in last4_fechas)

        # Ultima asistencia
        ultima_asistencia = max(fechas_asistidas) if fechas_asistidas else None

        # Racha actual: positivo = semanas asistidas consecutivas, negativo = semanas ausentes
        racha_actual = 0
        for h in reversed(historial):
            if racha_actual == 0:
                racha_actual = 1 if h["asistio"] else -1
            elif (racha_actual > 0) == h["asistio"]:
                racha_actual += 1 if h["asistio"] else -1
            else:
                break

        personas_list.append({
            "id": p["id"],
            "nombre_completo": p["nombre_completo"],
            "grupo_actual": grupo,
            "proyecto": get_proyecto(grupo),
            "rol": p["rol"],
            "tipo_miembro": p["tipo_miembro"],
            "es_miembro": p["es_miembro"],
            "tipo_grupo": p["tipo_grupo"],
            "fecha_ingreso": p.get("fecha_ingreso"),
            "sesiones": historial,
            "sesiones_grupo": historial_grupo,
            "total_sesiones": total_sesiones,
            "total_asistencias": total_asistencias,
            "pct_total": pct_total,
            "pct_q1": pct_q["Q1"],
            "pct_q2": pct_q["Q2"],
            "pct_q3": pct_q["Q3"],
            "asist_q1": asist_q["Q1"],
            "total_q1": total_q["Q1"],
            "asist_q2": asist_q["Q2"],
            "total_q2": total_q["Q2"],
            "asist_q3": asist_q["Q3"],
            "total_q3": total_q["Q3"],
            "status": status,
            "status_q1": status_q["Q1"],
            "status_q2": status_q["Q2"],
            "status_q3": status_q["Q3"],
            "at_risk": at_risk,
            "ultima_asistencia": ultima_asistencia,
            "racha_actual": racha_actual,
        })

    # ---------------------------------------------------------------------------
    # Agregados por GRUPO ACTUAL
    # ---------------------------------------------------------------------------
    grupos_stats: dict = defaultdict(lambda: {
        "total_asistencias": 0, "total_posibles": 0,
        "asist_q": {q: 0 for q in QUARTERS},
        "posibles_q": {q: 0 for q in QUARTERS},
        "status_dist": defaultdict(int),
        "tipo_grupo": "", "num_miembros_formales": 0, "num_total": 0,
    })

    for p in personas_list:
        g = p["grupo_actual"]
        s = grupos_stats[g]
        s["tipo_grupo"] = p.get("tipo_grupo", "")
        s["num_total"] += 1
        s["status_dist"][p["status"]] += 1
        if p["es_miembro"]:
            s["num_miembros_formales"] += 1

        for sesion in personas[p["id"]]["sesiones_raw"]:
            if not sesion["aplica_grupo"]:
                continue
            q = sesion["quarter"]
            s["total_posibles"] += 1
            s["posibles_q"][q] += 1
            if sesion["asistio"]:
                s["total_asistencias"] += 1
                s["asist_q"][q] += 1

    grupos_list = []
    for g, s in grupos_stats.items():
        pct = round(s["total_asistencias"] / s["total_posibles"] * 100, 1) if s["total_posibles"] > 0 else 0
        pct_q = {
            q: round(s["asist_q"][q] / s["posibles_q"][q] * 100, 1) if s["posibles_q"][q] > 0 else 0
            for q in QUARTERS
        }
        pct_membresia = round(s["num_miembros_formales"] / s["num_total"] * 100, 1) if s["num_total"] > 0 else 0
        fechas_grupo = sesiones_por_grupo.get(g, [])
        sesiones_q = {q: sum(1 for d in fechas_grupo if get_quarter(d) == q) for q in QUARTERS}
        grupos_list.append({
            "nombre": g,
            "proyecto": get_proyecto(g),
            "tipo_grupo": s["tipo_grupo"],
            "num_miembros": s["num_total"],
            "num_miembros_formales": s["num_miembros_formales"],
            "pct_membresia": pct_membresia,
            "pct_asistencia": pct,
            "pct_q1": pct_q["Q1"],
            "pct_q2": pct_q["Q2"],
            "pct_q3": pct_q["Q3"],
            # Conteos por quarter — para que el dashboard combine quarters (filtro global) con sumas simples.
            "asist_q1": s["asist_q"]["Q1"],
            "asist_q2": s["asist_q"]["Q2"],
            "asist_q3": s["asist_q"]["Q3"],
            "posibles_q1": s["posibles_q"]["Q1"],
            "posibles_q2": s["posibles_q"]["Q2"],
            "posibles_q3": s["posibles_q"]["Q3"],
            "sesiones_q1": sesiones_q["Q1"],
            "sesiones_q2": sesiones_q["Q2"],
            "sesiones_q3": sesiones_q["Q3"],
            "status_dist": dict(s["status_dist"]),
            "sesiones_totales": len(fechas_grupo),
        })

    grupos_list.sort(key=lambda x: x["pct_asistencia"], reverse=True)

    # ---------------------------------------------------------------------------
    # Agregados por tipo
    # ---------------------------------------------------------------------------
    tipo_stats: dict = defaultdict(lambda: {"asistencias": 0, "posibles": 0, "personas": 0})
    for p in personas_list:
        t = p.get("tipo_grupo", "Sin tipo")
        tipo_stats[t]["asistencias"] += p["total_asistencias"]
        tipo_stats[t]["posibles"] += p["total_sesiones"]
        tipo_stats[t]["personas"] += 1

    tipo_list = [
        {
            "tipo": t,
            "label": GROUP_TYPES.get(t, t),
            "personas": s["personas"],
            "pct_asistencia": round(s["asistencias"] / s["posibles"] * 100, 1) if s["posibles"] > 0 else 0,
        }
        for t, s in tipo_stats.items()
    ]

    # ---------------------------------------------------------------------------
    # Evolucion semanal
    # ---------------------------------------------------------------------------
    # Bottom-up desde personas, independiente de GROUP_START_DATES.
    person_active_from = {p["id"]: parse_date(p["fecha_ingreso"]) if p["fecha_ingreso"] else None
                         for p in personas_list}
    # Asistentes por fecha en un solo recorrido (en vez de re-escanear por cada fecha).
    asistentes_por_fecha = Counter(
        h["fecha"]
        for p in personas_list for h in p["sesiones"] if h["asistio"]
    )

    evolucion = []
    for d in sorted(all_sessions):
        iso = d.isoformat()
        asistentes = asistentes_por_fecha.get(iso, 0)
        total_aplica = sum(
            1 for p in personas_list
            if session_valid_for_group(d, p["grupo_actual"])
            and (person_active_from[p["id"]] is None or d >= person_active_from[p["id"]])
        )
        if total_aplica == 0:
            continue  # fecha que no aplica a nadie (ej. sesion aun sin asistencia cargada): no es un punto de 0%
        evolucion.append({
            "fecha": iso,
            "quarter": get_quarter(d),
            "evento": EVENTS.get(iso),
            "asistentes": asistentes,
            "total_aplica": total_aplica,
            "pct": round(asistentes / total_aplica * 100, 1) if total_aplica > 0 else 0,
        })

    # ---------------------------------------------------------------------------
    # Personas en riesgo
    # ---------------------------------------------------------------------------
    at_risk_list = [
        {
            "nombre_completo": p["nombre_completo"],
            "grupo_actual": p["grupo_actual"],
            "tipo_grupo": p["tipo_grupo"],
            "pct_total": p["pct_total"],
            "status": p["status"],
            "ultima_asistencia": p["ultima_asistencia"],
        }
        for p in personas_list if p["at_risk"]
    ]
    at_risk_list.sort(key=lambda x: (x["grupo_actual"], x["nombre_completo"]))

    # ---------------------------------------------------------------------------
    # KPIs
    # ---------------------------------------------------------------------------
    total_personas = len(personas_list)
    status_global: dict = defaultdict(int)
    for p in personas_list:
        status_global[p["status"]] += 1

    pct_global = round(
        sum(p["total_asistencias"] for p in personas_list) /
        sum(p["total_sesiones"] for p in personas_list) * 100, 1
    ) if personas_list else 0

    # ---------------------------------------------------------------------------
    # Output
    # ---------------------------------------------------------------------------
    output = {
        "generated_at": datetime.now().isoformat(),
        "fetched_at": fetched_at,
        "kpis": {
            "total_personas": total_personas,
            "pct_asistencia_global": pct_global,
            "status_dist": dict(status_global),
            "total_at_risk": len(at_risk_list),
        },
        "personas": sorted(personas_list, key=lambda x: x["pct_total"], reverse=True),
        "grupos": grupos_list,
        "tipos": tipo_list,
        "evolucion": evolucion,
        "at_risk": at_risk_list,
        "eventos": EVENTS,
    }

    output_path = TMP_DIR / "asistencia_processed.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("[OK] Procesamiento completo.")
    print(f"    Personas activas: {total_personas}")
    print(f"    % asistencia global: {pct_global}%")
    print(f"    Status: {dict(status_global)}")
    print(f"    En riesgo: {len(at_risk_list)}")
    print("    Guardado en .tmp/asistencia_processed.json")


if __name__ == "__main__":
    main()
