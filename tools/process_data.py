"""
Tool: process_data.py
Aplica las reglas de negocio y genera .tmp/asistencia_processed.json
listo para ser consumido por generate_dashboard.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"

# ---------------------------------------------------------------------------
# Reglas de negocio
# ---------------------------------------------------------------------------

EXCEPTIONS = {
    # 11/4: solo GDC BETTA, GDC BETTA VIAJEROS y GDC SIGMA tuvieron sesion
    "2026-04-11": {"todos_menos": ["GDC BETTA", "GDC BETTA VIAJEROS", "GDC SIGMA"]},
    # 2/5 y 23/5: GDC BETTA no tuvo sesion
    "2026-05-02": {"excluir": ["GDC BETTA"]},
    "2026-05-23": {"excluir": ["GDC BETTA"]},
    # 30/5: GDC BETTA VIAJEROS no tuvo sesion
    "2026-05-30": {"excluir": ["GDC BETTA VIAJEROS"]},
}

EVENTS = {
    "2026-02-28": "JADAK",
    "2026-03-14": "Montecamp",
    "2026-03-21": "Reencuentro Montecamp",
    "2026-05-02": "Apologética",
    "2026-05-16": "El Viaje",
}


GROUP_TYPES = {
    "GBU": "Grupos Universitarios",
    "GDA": "Grupos de Amistad",
    "GDC": "Grupos de Crecimiento",
}

# Grupos creados en el ciclo: sesiones cuentan desde su fecha de creación (inclusive).
GROUP_START_DATES: dict[str, date] = {
    "GDC LAMBDA": date(2026, 5, 16),
    "GDC NEW BETTA": date(2026, 5, 16),
}

STATUS_ORDER = ["Fiel", "Activo", "Inconstante", "Inactivo"]


def get_active_from(ingreso: date) -> date:
    """Sesiones cuentan desde esta fecha (inclusive)."""
    return ingreso


def get_quarter(d: date) -> str:
    return "Q1" if d.month <= 3 else "Q2"


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
    elif pct <= 50:
        return "Inconstante"
    elif pct <= 79:
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
        elif cl == "grupo" and "grupo_actual" not in col_map:
            col_map["grupo"] = col
        elif cl in ("nom_completo", "nombre_completo"):
            col_map["nombre"] = col
        elif "nombre" in cl and "grupo" not in cl and "nom_completo" not in cl:
            col_map.setdefault("nombre", col)
        elif "apellido" in cl:
            col_map["apellido"] = col
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
        elif cl == "status" or cl == "estado":
            col_map["status_raw"] = col

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
    group_af_map = {g: get_active_from(d) for g, d in GROUP_START_DATES.items()}

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
                "active_from": get_active_from(fi_date) if fi_date else None,
                "sesiones_raw": [],
            }

        quarter = get_quarter(session_date)
        evento = EVENTS.get(session_date.isoformat())
        personal_af = personas[persona_key].get("active_from")
        g_af = group_af_map.get(grupo_actual.upper())
        effective_af = max(personal_af, g_af) if personal_af and g_af else (personal_af or g_af)
        aplica = (session_applies_to_group(session_date, grupo_actual) and
                  (effective_af is None or session_date >= effective_af))
        personas[persona_key]["sesiones_raw"].append({
            "fecha": session_date.isoformat(),
            "quarter": quarter,
            "evento": evento,
            "aplica_denominador": aplica,
            "asistio": asistio,
        })

    # ---------------------------------------------------------------------------
    # Denominadores por grupo
    # ---------------------------------------------------------------------------
    grupos_set = {p["grupo_actual"] for p in personas.values()}
    sesiones_por_grupo: dict[str, list[date]] = {
        g: sorted(
            s for s in all_sessions
            if session_applies_to_group(s, g)
            and (g.upper() not in group_af_map or s >= group_af_map[g.upper()])
        )
        for g in grupos_set
    }

    # ---------------------------------------------------------------------------
    # Calcular estadisticas por persona
    # ---------------------------------------------------------------------------
    personas_list = []

    for persona_key, p in personas.items():
        grupo = p["grupo_actual"]
        sesiones_raw = p["sesiones_raw"]
        active_from = p.get("active_from")
        fechas_aplican = [
            d for d in sesiones_por_grupo.get(grupo, [])
            if active_from is None or d >= active_from
        ]
        fechas_asistidas = {s["fecha"] for s in sesiones_raw if s["asistio"]}

        total_sesiones = len(fechas_aplican)
        total_asistencias = len([s for s in sesiones_raw if s["aplica_denominador"] and s["asistio"]])
        pct_total = round(total_asistencias / total_sesiones * 100, 1) if total_sesiones > 0 else 0

        asist_q1 = len([s for s in sesiones_raw if s["quarter"] == "Q1" and s["aplica_denominador"] and s["asistio"]])
        total_q1 = len([d for d in fechas_aplican if get_quarter(d) == "Q1"])
        pct_q1 = round(asist_q1 / total_q1 * 100, 1) if total_q1 > 0 else 0

        asist_q2 = len([s for s in sesiones_raw if s["quarter"] == "Q2" and s["aplica_denominador"] and s["asistio"]])
        total_q2 = len([d for d in fechas_aplican if get_quarter(d) == "Q2"])
        pct_q2 = round(asist_q2 / total_q2 * 100, 1) if total_q2 > 0 else 0

        status = get_status(pct_total)
        status_q1 = get_status(pct_q1) if total_q1 > 0 else None
        status_q2 = get_status(pct_q2) if total_q2 > 0 else None

        # Historial completo
        historial = [
            {
                "fecha": d.isoformat(),
                "asistio": d.isoformat() in fechas_asistidas,
                "quarter": get_quarter(d),
                "evento": EVENTS.get(d.isoformat()),
            }
            for d in fechas_aplican
        ]

        # En riesgo: 0 asistencias en las ultimas 4 sesiones que aplican al grupo (dinamico)
        last4_fechas = {d.isoformat() for d in sorted(fechas_aplican)[-4:]}
        at_risk = len(last4_fechas) > 0 and not any(
            h["asistio"] for h in historial if h["fecha"] in last4_fechas
        )

        # Ultima asistencia
        fechas_asistidas_sorted = sorted(fechas_asistidas, reverse=True)
        ultima_asistencia = fechas_asistidas_sorted[0] if fechas_asistidas_sorted else None

        # Racha actual: positivo = semanas asistidas consecutivas, negativo = semanas ausentes
        hist_desc = sorted(historial, key=lambda x: x["fecha"], reverse=True)
        racha_actual = 0
        if hist_desc:
            going = hist_desc[0]["asistio"]
            for h in hist_desc:
                if h["asistio"] == going:
                    racha_actual += 1 if going else -1
                else:
                    break

        personas_list.append({
            "id": p["id"],
            "nombre_completo": p["nombre_completo"],
            "grupo_actual": grupo,
            "rol": p["rol"],
            "tipo_miembro": p["tipo_miembro"],
            "es_miembro": p["es_miembro"],
            "tipo_grupo": p["tipo_grupo"],
            "fecha_ingreso": p.get("fecha_ingreso"),
            "sesiones": historial,
            "total_sesiones": total_sesiones,
            "total_asistencias": total_asistencias,
            "pct_total": pct_total,
            "pct_q1": pct_q1,
            "pct_q2": pct_q2,
            "asist_q1": asist_q1,
            "total_q1": total_q1,
            "asist_q2": asist_q2,
            "total_q2": total_q2,
            "status": status,
            "status_q1": status_q1,
            "status_q2": status_q2,
            "at_risk": at_risk,
            "ultima_asistencia": ultima_asistencia,
            "racha_actual": racha_actual,
        })

    # ---------------------------------------------------------------------------
    # Agregados por GRUPO ACTUAL
    # ---------------------------------------------------------------------------
    grupos_stats: dict = defaultdict(lambda: {
        "total_asistencias": 0, "total_posibles": 0,
        "asist_q1": 0, "posibles_q1": 0,
        "asist_q2": 0, "posibles_q2": 0,
        "status_dist": defaultdict(int),
        "tipo_grupo": "", "num_miembros_formales": 0, "num_total": 0,
    })

    for p in personas_list:
        g = p["grupo_actual"]
        grupos_stats[g]["total_asistencias"] += p["total_asistencias"]
        grupos_stats[g]["total_posibles"] += p["total_sesiones"]
        grupos_stats[g]["asist_q1"] += p["asist_q1"]
        grupos_stats[g]["posibles_q1"] += p["total_q1"]
        grupos_stats[g]["asist_q2"] += p["asist_q2"]
        grupos_stats[g]["posibles_q2"] += p["total_q2"]
        grupos_stats[g]["status_dist"][p["status"]] += 1
        grupos_stats[g]["tipo_grupo"] = p.get("tipo_grupo", "")
        grupos_stats[g]["num_total"] += 1
        if p["es_miembro"]:
            grupos_stats[g]["num_miembros_formales"] += 1

    grupos_list = []
    for g, s in grupos_stats.items():
        pct = round(s["total_asistencias"] / s["total_posibles"] * 100, 1) if s["total_posibles"] > 0 else 0
        pct_q1 = round(s["asist_q1"] / s["posibles_q1"] * 100, 1) if s["posibles_q1"] > 0 else 0
        pct_q2 = round(s["asist_q2"] / s["posibles_q2"] * 100, 1) if s["posibles_q2"] > 0 else 0
        pct_membresia = round(s["num_miembros_formales"] / s["num_total"] * 100, 1) if s["num_total"] > 0 else 0
        grupos_list.append({
            "nombre": g,
            "tipo_grupo": s["tipo_grupo"],
            "num_miembros": s["num_total"],
            "num_miembros_formales": s["num_miembros_formales"],
            "pct_membresia": pct_membresia,
            "pct_asistencia": pct,
            "pct_q1": pct_q1,
            "pct_q2": pct_q2,
            "status_dist": dict(s["status_dist"]),
            "sesiones_totales": len(sesiones_por_grupo.get(g, [])),
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
    person_active_from = {}
    for p in personas_list:
        fi = p.get("fecha_ingreso")
        af = get_active_from(parse_date(fi)) if fi else None
        gs = GROUP_START_DATES.get(p["grupo_actual"].upper())
        if gs:
            gaf = get_active_from(gs)
            af = max(af, gaf) if af else gaf
        person_active_from[p["id"]] = af

    evolucion = []
    for d in sorted(all_sessions):
        asistentes = sum(
            1 for p in personas_list
            if any(h["fecha"] == d.isoformat() and h["asistio"] for h in p["sesiones"])
        )
        total_aplica = sum(
            1 for p in personas_list
            if session_applies_to_group(d, p["grupo_actual"])
            and (person_active_from[p["id"]] is None
                 or d >= person_active_from[p["id"]])
        )
        evolucion.append({
            "fecha": d.isoformat(),
            "quarter": get_quarter(d),
            "evento": EVENTS.get(d.isoformat()),
            "asistentes": asistentes,
            "total_aplica": total_aplica,
            "pct": round(asistentes / total_aplica * 100, 1) if total_aplica > 0 else 0,
        })

    # ---------------------------------------------------------------------------
    # Matriz de transicion Q1 -> Q2
    # ---------------------------------------------------------------------------
    status_matrix: dict = {s1: {s2: 0 for s2 in STATUS_ORDER} for s1 in STATUS_ORDER}
    for p in personas_list:
        s1 = p["status_q1"]
        s2 = p["status_q2"]
        if s1 and s2:
            status_matrix[s1][s2] += 1

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
        "status_matrix": status_matrix,
        "at_risk": at_risk_list,
        "eventos": EVENTS,
        "excepciones": {k: v for k, v in EXCEPTIONS.items()},
    }

    output_path = TMP_DIR / "asistencia_processed.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] Procesamiento completo.")
    print(f"    Personas activas: {total_personas}")
    print(f"    % asistencia global: {pct_global}%")
    print(f"    Status: {dict(status_global)}")
    print(f"    En riesgo: {len(at_risk_list)}")
    print(f"    Guardado en .tmp/asistencia_processed.json")


if __name__ == "__main__":
    main()
