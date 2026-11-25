"""Asistencia v2 (tool general): motor de cálculo con la lente "grupo actual hacia atrás" (la lógica principal, igual al sistema viejo).
Entradas ya cargadas (sin Drive): reglas (Reglas), personas del maestro vigente, registros y asistentes del Fact.
Salida: dict con la misma estructura que el `asistencia_processed.json` del sistema viejo (para la paridad) más `dni` por persona.
Niveles (igual que el sistema viejo): persona (solo su FECHA_INGRESO), grupo (además la fecha de inicio del grupo) y global (desde personas).
Población = personas del maestro vigente con GRUPO_ACTUAL (sin grupo actual no existe). La asistencia es el conjunto (sábado, persona).
"""
import datetime
from collections import Counter, defaultdict


def _historial(R, fechas, asistidas, acreditadas):
    return [{"fecha": d.isoformat(), "asistio": d in asistidas, "acreditada": d in acreditadas, "quarter": R.quarter(d), "evento": R.eventos.get(d.isoformat())} for d in fechas]


def calcular(R, alias, personas_maestro, registros, asistentes, hasta=None, generado=None, meses_acreditados=None):
    """`personas_maestro`: filas del maestro vigente (dicts con DNI, NOM_COMPLETO, GRUPO_ACTUAL, TIPO_GRUPO, ROL_ACTUAL, TIPO_MIEMBRO, FECHA_INGRESO).
    `registros`/`asistentes`: tablas del Fact (dicts; fechas ISO). `hasta`: ignora sesiones posteriores (para comparar con una corrida vieja).
    `meses_acreditados`: {dni: {'AAAA-MM'}} meses en que la persona tuvo el tipo que cuenta como asistencia (8. Mentores, ver asistencia_carga.meses_acreditados):
    toda sesión de su grupo actual en esos meses le aplica y cuenta como asistida. No crea sesiones: si hubo reunión se decide solo con asistencia real."""
    meses_acreditados = meses_acreditados or {}
    # --- población y asistencia efectiva ---
    poblacion = {}
    for x in personas_maestro:
        if not x.get("GRUPO_ACTUAL"):
            continue
        gid = alias.grupo(x["GRUPO_ACTUAL"])
        if gid is None:
            raise ValueError(f"Grupo del maestro que no está en la tabla grupos: {x['GRUPO_ACTUAL']!r}")
        poblacion[str(x["DNI"])] = {"m": x, "gid": gid}

    fecha_de = {}
    for r in registros:
        if r["vigente"] in (1, "1"):
            d = datetime.date.fromisoformat(r["sabado"])
            if hasta is None or d <= hasta:
                fecha_de[r["registro_id"]] = d
    todas = sorted(set(fecha_de.values()))
    asistio = defaultdict(set)  # dni -> fechas de sesión asistidas (cualquier fecha)
    for a in asistentes:
        d = fecha_de.get(a["registro_id"])
        if d is not None:
            asistio[str(a["dni"])].add(d)

    asist_gf = Counter()  # (grupo_id, fecha) -> personas del grupo actual que asistieron DE VERDAD (lo acreditado no cuenta para saber si hubo reunión)
    for dni, p in poblacion.items():
        for d in asistio.get(dni, ()):
            asist_gf[(p["gid"], d)] += 1

    grupos_set = {p["gid"] for p in poblacion.values()}
    ses_persona = {g: sorted(d for d in todas if R.sesion_valida(d, g, asist_gf)) for g in grupos_set}  # sin fecha de inicio del grupo
    ses_grupo = {g: [d for d in ses_persona[g] if R.inicio.get(g) is None or d >= R.inicio[g]] for g in grupos_set}

    # --- personas ---
    plist, por_dni = [], {}
    for dni, p in poblacion.items():
        m, gid = p["m"], p["gid"]
        nom_grupo = R.grupos[gid]["nombre"]
        af = m.get("FECHA_INGRESO")
        reales, meses = asistio.get(dni, set()), meses_acreditados.get(dni, ())
        mentoria = {d for d in ses_persona[gid] if d.strftime("%Y-%m") in meses}
        asistidas, acreditadas = reales | mentoria, mentoria - reales
        fechas = [d for d in ses_persona[gid] if af is None or d >= af or d in mentoria]
        fechas_g = [d for d in ses_grupo[gid] if af is None or d >= af or d in mentoria]
        asist_q = {q[0]: 0 for q in R.quarters}
        total_q = {q[0]: 0 for q in R.quarters}
        for d in fechas:
            total_q[R.quarter(d)] += 1
            if d in asistidas:
                asist_q[R.quarter(d)] += 1
        total_asist = sum(asist_q.values())
        total_ses = len(fechas)
        pct = round(total_asist / total_ses * 100, 1) if total_ses else 0
        pct_q = {q: round(asist_q[q] / total_q[q] * 100, 1) if total_q[q] else 0 for q in asist_q}
        hist = _historial(R, fechas, asistidas, acreditadas)
        ultimas = hist[-R.ventana_riesgo:]
        at_risk = len(ultimas) >= R.ventana_riesgo and not any(h["asistio"] for h in ultimas)  # quien tiene menos de N sesiones no está en riesgo (cambio del 2026-11-21)
        racha = 0
        for h in reversed(hist):
            if racha == 0:
                racha = 1 if h["asistio"] else -1
            elif (racha > 0) == h["asistio"]:
                racha += 1 if h["asistio"] else -1
            else:
                break
        tipo = next((k for k in ("GBU", "GDA", "GDC") if k in (m.get("TIPO_GRUPO") or "").upper()), (m.get("TIPO_GRUPO") or ""))
        reg = {
            "id": dni, "dni": dni, "nombre_completo": m["NOM_COMPLETO"], "grupo_actual": nom_grupo, "grupo_id": gid,
            "proyecto": R.grupos[gid]["proyecto"], "rol": m.get("ROL_ACTUAL") or "", "tipo_miembro": m.get("TIPO_MIEMBRO") or "",
            "es_miembro": R.es_miembro(m.get("TIPO_MIEMBRO")), "tipo_grupo": tipo, "fecha_ingreso": af.isoformat() if af else None,
            "sesiones": hist, "sesiones_grupo": _historial(R, fechas_g, asistidas, acreditadas), "total_sesiones": total_ses, "total_asistencias": total_asist,
            "pct_total": pct, "status": R.status(pct), "at_risk": at_risk,
            "ultima_asistencia": max(asistidas).isoformat() if asistidas else None, "racha_actual": racha}
        for q in asist_q:
            ql = q.lower()
            reg[f"pct_{ql}"], reg[f"asist_{ql}"], reg[f"total_{ql}"] = pct_q[q], asist_q[q], total_q[q]
            reg[f"status_{ql}"] = R.status(pct_q[q]) if total_q[q] else None
        reg["_aplica_grupo"] = set(fechas_g)  # nivel grupo: sesiones válidas desde el inicio del grupo y del ingreso
        reg["_asistidas"] = asistidas
        plist.append(reg)
        por_dni[dni] = reg

    # --- grupos ---
    gs = defaultdict(lambda: {"asist": 0, "pos": 0, "aq": Counter(), "pq": Counter(), "sd": Counter(), "n": 0, "formales": 0})
    for p in plist:
        s = gs[p["grupo_id"]]
        s["n"] += 1
        s["sd"][p["status"]] += 1
        s["formales"] += p["es_miembro"]
        for d in p["_aplica_grupo"]:
            q = R.quarter(d)
            s["pos"] += 1
            s["pq"][q] += 1
            if d in p["_asistidas"]:
                s["asist"] += 1
                s["aq"][q] += 1
    grupos = []
    for gid, s in gs.items():
        g = R.grupos[gid]
        fechas_g = ses_grupo[gid]
        o = {"nombre": g["nombre"], "grupo_id": gid, "proyecto": g["proyecto"], "tipo_grupo": g["tipo"], "num_miembros": s["n"],
             "num_miembros_formales": s["formales"], "pct_membresia": round(s["formales"] / s["n"] * 100, 1) if s["n"] else 0,
             "pct_asistencia": round(s["asist"] / s["pos"] * 100, 1) if s["pos"] else 0, "status_dist": dict(s["sd"]), "sesiones_totales": len(fechas_g)}
        for q, *_ in R.quarters:
            ql = q.lower()
            o[f"pct_{ql}"] = round(s["aq"][q] / s["pq"][q] * 100, 1) if s["pq"][q] else 0
            o[f"asist_{ql}"], o[f"posibles_{ql}"] = s["aq"][q], s["pq"][q]
            o[f"sesiones_{ql}"] = sum(1 for d in fechas_g if R.quarter(d) == q)
        grupos.append(o)
    grupos.sort(key=lambda x: x["pct_asistencia"], reverse=True)

    # --- tipos, evolución, riesgo, kpis ---
    tstats = defaultdict(lambda: [0, 0, 0])
    for p in plist:
        t = tstats[p["tipo_grupo"] or "Sin tipo"]
        t[0] += p["total_asistencias"]; t[1] += p["total_sesiones"]; t[2] += 1
    etiquetas = {"GBU": "Grupos Universitarios", "GDA": "Grupos de Amistad", "GDC": "Grupos de Crecimiento"}
    tipos = [{"tipo": t, "label": etiquetas.get(t, t), "personas": v[2], "pct_asistencia": round(v[0] / v[1] * 100, 1) if v[1] else 0} for t, v in tstats.items()]

    asist_fecha = Counter(h["fecha"] for p in plist for h in p["sesiones"] if h["asistio"])
    aplica_fecha = Counter(h["fecha"] for p in plist for h in p["sesiones"])
    evolucion = []
    for d in todas:
        total = aplica_fecha.get(d.isoformat(), 0)
        if total == 0:
            continue
        a = asist_fecha.get(d.isoformat(), 0)
        evolucion.append({"fecha": d.isoformat(), "quarter": R.quarter(d), "evento": R.eventos.get(d.isoformat()), "asistentes": a, "total_aplica": total, "pct": round(a / total * 100, 1)})

    en_riesgo = sorted(({"nombre_completo": p["nombre_completo"], "grupo_actual": p["grupo_actual"], "tipo_grupo": p["tipo_grupo"], "pct_total": p["pct_total"],
                         "status": p["status"], "ultima_asistencia": p["ultima_asistencia"]} for p in plist if p["at_risk"]), key=lambda x: (x["grupo_actual"], x["nombre_completo"]))
    sd = Counter(p["status"] for p in plist)
    pct_global = round(sum(p["total_asistencias"] for p in plist) / sum(p["total_sesiones"] for p in plist) * 100, 1) if plist else 0
    for p in plist:
        p.pop("_aplica_grupo"); p.pop("_asistidas")
    return {"generated_at": generado or datetime.datetime.now().isoformat(),
            "kpis": {"total_personas": len(plist), "pct_asistencia_global": pct_global, "status_dist": dict(sd), "total_at_risk": len(en_riesgo)},
            "personas": sorted(plist, key=lambda x: x["pct_total"], reverse=True), "grupos": grupos, "tipos": tipos, "evolucion": evolucion,
            "at_risk": en_riesgo, "eventos": R.eventos}
