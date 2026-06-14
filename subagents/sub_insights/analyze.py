#!/usr/bin/env python3
"""
Sub-agente: sub_insights
Análisis profundo del reporte de asistencia J1.

Lee:    .tmp/asistencia_processed.json
Escribe: subagents/sub_insights/reports/insights_report_YYYY-MM-DD.md
          subagents/sub_insights/reports/insights_report_YYYY-MM-DD.html

Lógica: único recorrido sobre personas → acumula todo en dicts →
        computa insights → genera ambos archivos.
"""

import json
import os
from datetime import date
from pathlib import Path
from collections import defaultdict

# ── Rutas ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
INPUT = ROOT / ".tmp" / "asistencia_processed.json"
REPORTS = Path(__file__).parent / "reports"
TODAY = date.today().isoformat()
OUT_MD = REPORTS / f"insights_report_{TODAY}.md"
OUT_HTML = REPORTS / f"insights_report_{TODAY}.html"
REPORTS.mkdir(exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def pct(a, b):
    return round(a / b * 100, 1) if b else None


def fp(v, suffix=""):
    return f"{v:.1f}{suffix}" if v is not None else "—"


def delta_label(d):
    if d is None:
        return "—"
    sign = "▲" if d > 0 else "▼" if d < 0 else "→"
    return f"{sign} {abs(d):.1f}%"


TIPO_NOMBRE = {"GBU": "Universitario", "GDA": "Amistad", "GDC": "Crecimiento"}
STATUS_ORDER = ["Fiel", "Activo", "Inconstante", "Inactivo"]


# ── Carga ────────────────────────────────────────────────────────────────────
with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

personas = data["personas"]
kpis = data["kpis"]
fecha_reporte = data.get("generated_at", "")[:10]


# ── Único recorrido ──────────────────────────────────────────────────────────
grupos = defaultdict(lambda: dict(
    tipo="", miembros=0,
    asist_total=0, sesiones_total=0,
    asist_q1=0, total_q1=0,
    asist_q2=0, total_q2=0,
    at_risk=0,
))
roles = defaultdict(lambda: dict(asist=0, total=0, n=0))
fechas = defaultdict(lambda: dict(asistencias=0, total=0, evento=None))
momentum = defaultdict(int)

backbone = []        # excluye Mentores y Comentores
criticos = defaultdict(list)
nuevos = []
mentores_alerta = []

for p in personas:
    g = p["grupo_actual"]
    gr = grupos[g]
    gr["tipo"] = p["tipo_grupo"]
    gr["miembros"] += 1
    gr["asist_total"] += p["total_asistencias"]
    gr["sesiones_total"] += p["total_sesiones"]
    gr["asist_q1"] += p["asist_q1"]
    gr["total_q1"] += p["total_q1"]
    gr["asist_q2"] += p["asist_q2"]
    gr["total_q2"] += p["total_q2"]
    if p["at_risk"]:
        gr["at_risk"] += 1

    rol = (p.get("rol") or "Sin rol").strip() or "Sin rol"
    roles[rol]["asist"] += p["total_asistencias"]
    roles[rol]["total"] += p["total_sesiones"]
    roles[rol]["n"] += 1

    for s in p["sesiones"]:
        fd = s["fecha"]
        fechas[fd]["total"] += 1
        if s["asistio"]:
            fechas[fd]["asistencias"] += 1
        if s.get("evento") and fechas[fd]["evento"] is None:
            fechas[fd]["evento"] = s["evento"]

    if p["total_q1"] > 0 and p["total_q2"] > 0:
        sq1 = p.get("status_q1") or "Inactivo"
        sq2 = p.get("status_q2") or "Inactivo"
        momentum[(sq1, sq2)] += 1

    # Columna vertebral: excluye Mentores y Comentores — se filtra a top 15 en post-procesamiento
    if rol not in ("Mentor", "Comentor"):
        backbone.append(dict(
            nombre=p["nombre_completo"], grupo=g,
            pct=p["pct_total"], racha=p["racha_actual"],
            pct_q1=p["pct_q1"], pct_q2=p["pct_q2"],
        ))

    if p["racha_actual"] <= -4:
        criticos[g].append(dict(
            nombre=p["nombre_completo"],
            racha=p["racha_actual"],
            pct=p["pct_total"],
        ))

    if p.get("fecha_ingreso"):
        nuevos.append(dict(
            nombre=p["nombre_completo"], grupo=g,
            fecha_ingreso=p["fecha_ingreso"],
            pct_q2=p["pct_q2"],
            status_q2=p.get("status_q2") or p["status"],
            at_risk=p["at_risk"],
            racha=p["racha_actual"],
        ))

    if rol in ("Mentor", "Comentor") and p["pct_total"] < 60:
        mentores_alerta.append(dict(
            nombre=p["nombre_completo"], rol=rol, grupo=g,
            pct=p["pct_total"], racha=p["racha_actual"],
        ))


# ── Post-procesamiento ───────────────────────────────────────────────────────
grupos_calc = {}
for nombre, gr in grupos.items():
    pct_global = pct(gr["asist_total"], gr["sesiones_total"])
    pct_q1 = pct(gr["asist_q1"], gr["total_q1"])
    pct_q2 = pct(gr["asist_q2"], gr["total_q2"])
    delta = round(pct_q2 - pct_q1, 1) if pct_q1 is not None and pct_q2 is not None else None
    at_risk_pct = pct(gr["at_risk"], gr["miembros"])
    grupos_calc[nombre] = dict(
        tipo=TIPO_NOMBRE.get(gr["tipo"], gr["tipo"]),
        miembros=gr["miembros"],
        pct_global=pct_global,
        pct_q1=pct_q1,
        pct_q2=pct_q2,
        delta=delta,
        at_risk=gr["at_risk"],
        at_risk_pct=at_risk_pct,
    )

grupos_sorted = sorted(grupos_calc.items(), key=lambda x: x[1]["pct_global"] or 0, reverse=True)

event_pcts, normal_pcts = [], []
for fecha_val, fd in sorted(fechas.items()):
    p_val = pct(fd["asistencias"], fd["total"])
    if p_val is None:
        continue
    if fd["evento"]:
        event_pcts.append((fecha_val, fd["evento"], p_val, fd["asistencias"], fd["total"]))
    else:
        normal_pcts.append((fecha_val, p_val, fd["asistencias"], fd["total"]))

avg_normal = round(sum(x[1] for x in normal_pcts) / len(normal_pcts), 1) if normal_pcts else None
sesiones_debiles = sorted(normal_pcts, key=lambda x: x[1])[:3]

backbone.sort(key=lambda x: (-x["pct"], -x["racha"]))
backbone = backbone[:15]

for gname in criticos:
    criticos[gname].sort(key=lambda x: x["racha"])

nuevos.sort(key=lambda x: x["pct_q2"] or 0)
mentores_alerta.sort(key=lambda x: x["pct"])

roles_sorted = sorted(
    [(r, v) for r, v in roles.items() if v["total"] > 0],
    key=lambda x: pct(x[1]["asist"], x[1]["total"]) or 0,
    reverse=True,
)

mejoras = sum(v for (s1, s2), v in momentum.items()
              if STATUS_ORDER.index(s1) > STATUS_ORDER.index(s2))
caidas = sum(v for (s1, s2), v in momentum.items()
             if STATUS_ORDER.index(s1) < STATUS_ORDER.index(s2))
estables = sum(v for (s1, s2), v in momentum.items() if s1 == s2)
total_momentum = mejoras + caidas + estables

# ── Insights clave ────────────────────────────────────────────────────────────
pct_q1_global = pct(
    sum(gr["asist_q1"] for gr in grupos.values()),
    sum(gr["total_q1"] for gr in grupos.values()),
)
pct_q2_global = pct(
    sum(gr["asist_q2"] for gr in grupos.values()),
    sum(gr["total_q2"] for gr in grupos.values()),
)
delta_global = round(pct_q2_global - pct_q1_global, 1) if pct_q1_global and pct_q2_global else None

grupos_con_delta = [(n, g) for n, g in grupos_calc.items() if g["delta"] is not None]
top_mejora = max(grupos_con_delta, key=lambda x: x[1]["delta"]) if grupos_con_delta else None
top_caida = min(grupos_con_delta, key=lambda x: x[1]["delta"]) if grupos_con_delta else None
top_riesgo = max(grupos_calc.items(), key=lambda x: x[1]["at_risk_pct"] or 0) if grupos_calc else None
grupos_alerta = [(n, g) for n, g in grupos_calc.items() if (g["at_risk_pct"] or 0) > 40]

best_event = max(event_pcts, key=lambda x: x[2]) if event_pcts and avg_normal else None
pct_risk_global = pct(kpis["total_at_risk"], kpis["total_personas"])

# Construir lista de insights: (tipo, texto) — tipo: "pos" | "neg" | "neu"
key_insights = []

if delta_global is not None:
    if delta_global > 2:
        key_insights.append(("pos", f"Tendencia positiva: la asistencia global subió {delta_global}% de Q1 a Q2 ({fp(pct_q1_global)}% → {fp(pct_q2_global)}%)"))
    elif delta_global < -2:
        key_insights.append(("neg", f"Tendencia negativa: la asistencia global cayó {abs(delta_global)}% de Q1 a Q2 ({fp(pct_q1_global)}% → {fp(pct_q2_global)}%)"))
    else:
        key_insights.append(("neu", f"Asistencia estable entre quarters: Q1 {fp(pct_q1_global)}% → Q2 {fp(pct_q2_global)}% (variación mínima de {delta_global}%)"))

if top_mejora:
    key_insights.append(("pos", f"Grupo con mayor mejora Q1→Q2: {top_mejora[0]} (+{top_mejora[1]['delta']}%, ahora en {fp(top_mejora[1]['pct_q2'])}%)"))

if top_caida and top_caida[1]["delta"] is not None and top_caida[1]["delta"] < -3:
    key_insights.append(("neg", f"Grupo con mayor caída Q1→Q2: {top_caida[0]} ({top_caida[1]['delta']}%, ahora en {fp(top_caida[1]['pct_q2'])}%)"))

for gn, ga in sorted(grupos_alerta, key=lambda x: -(x[1]["at_risk_pct"] or 0))[:2]:
    key_insights.append(("neg", f"Concentración de riesgo en {gn}: {ga['at_risk']}/{ga['miembros']} miembros en riesgo ({fp(ga['at_risk_pct'])}%)"))

if pct_risk_global and pct_risk_global > 25:
    key_insights.append(("neg", f"{kpis['total_at_risk']} personas en riesgo ({fp(pct_risk_global)}% del total) — nivel de alerta elevado"))
elif pct_risk_global:
    key_insights.append(("neu", f"{kpis['total_at_risk']} personas en riesgo ({fp(pct_risk_global)}% del total)"))

if total_momentum > 0:
    if mejoras > caidas * 1.3:
        key_insights.append(("pos", f"Buen momentum entre quarters: {mejoras} personas mejoraron de categoría vs {caidas} que cayeron"))
    elif caidas > mejoras * 1.3:
        key_insights.append(("neg", f"Momentum preocupante: {caidas} personas cayeron de categoría entre Q1 y Q2 vs {mejoras} que mejoraron"))
    else:
        key_insights.append(("neu", f"Momentum equilibrado entre quarters: {mejoras} mejoraron, {caidas} cayeron, {estables} estables"))

if best_event and avg_normal:
    ev_delta = round(best_event[2] - avg_normal, 1)
    if ev_delta > 5:
        key_insights.append(("pos", f"Evento de mayor impacto: {best_event[1]} ({best_event[0]}) con {fp(best_event[2])}% asistencia (+{ev_delta}% sobre el promedio)"))

if grupos_sorted:
    top_g = grupos_sorted[0]
    key_insights.append(("pos", f"Grupo más comprometido del ciclo: {top_g[0]} con {fp(top_g[1]['pct_global'])}% asistencia global"))

# ── Resumen nuevos ingresos ───────────────────────────────────────────────────
ni_en_riesgo = [n for n in nuevos if n["at_risk"]]
ni_buen_arranque = [n for n in nuevos if (n["pct_q2"] or 0) >= 70]
ni_seguimiento = [n for n in nuevos if n["at_risk"] or n["racha"] <= -2]
ni_medio = [n for n in nuevos if not n["at_risk"] and (n["pct_q2"] or 0) < 70]
ni_prom_q2 = round(sum(n["pct_q2"] or 0 for n in nuevos) / len(nuevos), 1) if nuevos else 0


# ── Generación Markdown ──────────────────────────────────────────────────────
def build_md():
    lines = []
    a = lines.append

    a("# Insights Report — J1 Asistencia")
    a(f"_Generado: {fecha_reporte}_\n")

    # 0. KPIs + Insights Clave
    a("## 0. KPIs Globales e Insights Clave\n")
    sd = kpis["status_dist"]
    a("| Métrica | Valor |")
    a("|---------|-------|")
    a(f"| Total personas | {kpis['total_personas']} |")
    a(f"| % Asistencia global | {kpis['pct_asistencia_global']}% |")
    a(f"| Fieles | {sd.get('Fiel', 0)} ({fp(pct(sd.get('Fiel',0), kpis['total_personas']))}%) |")
    a(f"| Activos | {sd.get('Activo', 0)} ({fp(pct(sd.get('Activo',0), kpis['total_personas']))}%) |")
    a(f"| Inconstantes | {sd.get('Inconstante', 0)} ({fp(pct(sd.get('Inconstante',0), kpis['total_personas']))}%) |")
    a(f"| Inactivos | {sd.get('Inactivo', 0)} ({fp(pct(sd.get('Inactivo',0), kpis['total_personas']))}%) |")
    a(f"| En riesgo total | {kpis['total_at_risk']} ({fp(pct(kpis['total_at_risk'], kpis['total_personas']))}%) |")
    a("")
    a("### Insights Clave\n")
    ICON = {"pos": "▲", "neg": "▼", "neu": "→"}
    for tipo, texto in key_insights:
        a(f"- {ICON[tipo]} {texto}")
    a("")

    # 1. Semáforo de grupos
    a("## 1. Semáforo de Grupos\n")
    a("| Grupo | Tipo | N | % Global | Q1% | Q2% | Δ Q1→Q2 | En Riesgo |")
    a("|-------|------|---|----------|-----|-----|---------|-----------|")
    for nombre, g in grupos_sorted:
        a(f"| {nombre} | {g['tipo']} | {g['miembros']} | {fp(g['pct_global'])}% "
          f"| {fp(g['pct_q1'])}% | {fp(g['pct_q2'])}% "
          f"| {delta_label(g['delta'])} | {g['at_risk']} ({fp(g['at_risk_pct'])}%) |")
    a("")

    # 2. Momentum Q1→Q2
    a("## 2. Momentum Individual Q1→Q2\n")
    a(f"_Solo personas con sesiones en ambos quarters. Total: {total_momentum} personas._\n")
    a(f"- **Mejoraron** (subieron de categoría): {mejoras} ({fp(pct(mejoras, total_momentum))}%)")
    a(f"- **Se mantuvieron** en misma categoría: {estables} ({fp(pct(estables, total_momentum))}%)")
    a(f"- **Cayeron** (bajaron de categoría): {caidas} ({fp(pct(caidas, total_momentum))}%)")
    a("")
    a("**Matriz de transición** (filas = Q1, columnas = Q2):\n")
    a("| Q1 \\ Q2 | Fiel | Activo | Inconstante | Inactivo |")
    a("|---------|------|--------|-------------|----------|")
    for s1 in STATUS_ORDER:
        row = [str(momentum.get((s1, s2), 0)) for s2 in STATUS_ORDER]
        a(f"| **{s1}** | {' | '.join(row)} |")
    a("")
    grandes_caidas = [(s1, s2, v) for (s1, s2), v in momentum.items()
                      if STATUS_ORDER.index(s2) - STATUS_ORDER.index(s1) >= 2 and v > 0]
    grandes_mejoras = [(s1, s2, v) for (s1, s2), v in momentum.items()
                       if STATUS_ORDER.index(s1) - STATUS_ORDER.index(s2) >= 2 and v > 0]
    if grandes_caidas:
        a("**Caídas drásticas** (saltaron 2+ categorías):")
        for s1, s2, v in sorted(grandes_caidas, key=lambda x: -x[2]):
            a(f"- {s1} → {s2}: {v} personas")
        a("")
    if grandes_mejoras:
        a("**Recuperaciones notables** (subieron 2+ categorías):")
        for s1, s2, v in sorted(grandes_mejoras, key=lambda x: -x[2]):
            a(f"- {s1} → {s2}: {v} personas")
        a("")

    # 3. Columna Vertebral
    a("## 3. Columna Vertebral — Top 15 (excluye Mentores y Comentores)\n")
    a(f"_Las 15 personas con mejor asistencia total del ciclo._\n")
    if backbone:
        a("| # | Persona | Grupo | % Total | Q1% | Q2% | Racha |")
        a("|---|---------|-------|---------|-----|-----|-------|")
        for i, b in enumerate(backbone, 1):
            a(f"| {i} | {b['nombre']} | {b['grupo']} | {fp(b['pct'])}% | {fp(b['pct_q1'])}% | {fp(b['pct_q2'])}% | +{b['racha']} |")
    a("")

    # 4. Alertas Críticas
    total_criticos = sum(len(v) for v in criticos.values())
    a("## 4. Alertas Críticas (racha ≤ -4)\n")
    a(f"_Personas ausentes 4 o más sesiones consecutivas. Total: {total_criticos}_\n")
    for gname in sorted(criticos.keys()):
        lista = criticos[gname]
        a(f"**{gname}** ({len(lista)} personas):")
        for c in lista:
            a(f"- {c['nombre']} — racha {c['racha']}, % total {fp(c['pct'])}%")
        a("")

    # 5. Impacto de Eventos
    a("## 5. Impacto de Eventos\n")
    a(f"_Promedio sesiones normales: {fp(avg_normal)}%_\n")
    a("| Fecha | Evento | % Asistencia | Δ vs Normal | Presentes |")
    a("|-------|--------|-------------|-------------|-----------|")
    for fecha_val, ev, p_ev, asist, total_f in sorted(event_pcts):
        delta_ev = round(p_ev - avg_normal, 1) if avg_normal else None
        a(f"| {fecha_val} | {ev} | {fp(p_ev)}% | {delta_label(delta_ev)} | {asist}/{total_f} |")
    a("")

    # 6. Sesiones más Débiles
    a("## 6. Sesiones más Débiles\n")
    a("| Fecha | % Asistencia | Presentes |")
    a("|-------|-------------|-----------|")
    for fecha_val, p_val, asist, total_f in sesiones_debiles:
        a(f"| {fecha_val} | {fp(p_val)}% | {asist}/{total_f} |")
    a("")

    # 7. Análisis por Rol
    a("## 7. Análisis por Rol\n")
    a("| Rol | N | % Asistencia |")
    a("|-----|---|-------------|")
    for rol_name, rv in roles_sorted:
        rp = pct(rv["asist"], rv["total"])
        a(f"| {rol_name} | {rv['n']} | {fp(rp)}% |")
    a("")
    if mentores_alerta:
        a(f"**Mentores/Comentores con < 60% asistencia** ({len(mentores_alerta)}):")
        for m in mentores_alerta:
            a(f"- {m['nombre']} ({m['rol']}) — {m['grupo']} — {fp(m['pct'])}% — racha {m['racha']}")
        a("")

    # 8. Nuevos Ingresos
    a("## 8. Nuevos Ingresos (FECHA_INGRESO)\n")
    a(f"_Total: {len(nuevos)} personas con fecha de ingreso registrada._\n")
    if nuevos:
        a("| Persona | Grupo | Ingreso | Q2% | Status Q2 | En Riesgo | Racha |")
        a("|---------|-------|---------|-----|-----------|-----------|-------|")
        for n in nuevos:
            riesgo = "⚠️ Sí" if n["at_risk"] else "No"
            a(f"| {n['nombre']} | {n['grupo']} | {n['fecha_ingreso']} "
              f"| {fp(n['pct_q2'])}% | {n['status_q2']} | {riesgo} | {n['racha']} |")
        a("")
        a("### Seguimiento Nuevos Ingresos\n")
        a(f"- **Promedio Q2:** {fp(ni_prom_q2)}% de asistencia desde su ingreso")
        a(f"- **En riesgo:** {len(ni_en_riesgo)} de {len(nuevos)} ({fp(pct(len(ni_en_riesgo), len(nuevos)))}%)")
        a(f"- **Buen arranque (Q2 >= 70%):** {len(ni_buen_arranque)} persona(s)")
        if ni_buen_arranque:
            a("  " + ", ".join(n["nombre"] for n in ni_buen_arranque))
        a(f"- **Requieren seguimiento** (en riesgo o racha <= -2): {len(ni_seguimiento)} persona(s)")
        if ni_seguimiento:
            for n in ni_seguimiento:
                a(f"  - {n['nombre']} ({n['grupo']}) — Q2: {fp(n['pct_q2'])}%, racha: {n['racha']}")
        if len(ni_en_riesgo) == 0 and ni_prom_q2 >= 60:
            a(f"\n_Diagnóstico: Los nuevos ingresos muestran un arranque sólido. Ninguno está en riesgo y el promedio Q2 de {fp(ni_prom_q2)}% es alentador._")
        elif len(ni_en_riesgo) > len(nuevos) / 2:
            a(f"\n_Diagnóstico: Más de la mitad de los nuevos ingresos ya están en riesgo. Se recomienda seguimiento pastoral activo en las próximas semanas._")
        else:
            a(f"\n_Diagnóstico: Arranque mixto. {len(ni_buen_arranque)} con buen ritmo, {len(ni_en_riesgo)} en riesgo. Priorizar acompañamiento de quienes aún no se consolidan._")
    a("")

    return "\n".join(lines)


# ── Generación HTML ──────────────────────────────────────────────────────────
def th(text):
    return f'<th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">{text}</th>'


def td(text, cls=""):
    return f'<td class="px-6 py-4 text-sm text-slate-700 {cls}">{text}</td>'


def delta_badge(d):
    if d is None:
        return '<span class="text-slate-400">—</span>'
    if d > 3:
        return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700">▲ {d:.1f}%</span>'
    if d < -3:
        return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700">▼ {abs(d):.1f}%</span>'
    return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">→ {d:.1f}%</span>'


def risk_cell(at_risk):
    if at_risk:
        return "<td class='px-6 py-4'><span class='text-rose-600 font-semibold'>&#9888; S&#237;</span></td>"
    return "<td class='px-6 py-4'><span class='text-slate-400'>No</span></td>"


def racha_cell(racha):
    cls = "text-emerald-600" if racha > 0 else "text-rose-600"
    return f"<td class='px-6 py-4 text-sm font-medium {cls}'>{racha}</td>"


def row_tint(delta):
    if delta is not None and delta > 5:
        return "bg-emerald-50/30"
    if delta is not None and delta < -5:
        return "bg-rose-50/30"
    return ""


def section(title, num, content):
    return f"""
<section class="bg-white border border-slate-100 rounded-2xl shadow-sm shadow-slate-100/70 overflow-hidden mb-6">
  <div class="px-6 py-4 border-b border-slate-100 flex items-center gap-3">
    <span class="flex-shrink-0 w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 text-xs font-bold flex items-center justify-center">{num}</span>
    <h2 class="text-base font-semibold text-slate-900">{title}</h2>
  </div>
  <div class="p-6">{content}</div>
</section>"""


def insight_bullet(tipo, texto):
    cfg = {
        "pos": ("bg-emerald-500", "text-emerald-800", "▲"),
        "neg": ("bg-rose-500", "text-rose-800", "▼"),
        "neu": ("bg-slate-400", "text-slate-700", "→"),
    }
    dot_cls, text_cls, icon = cfg[tipo]
    return (
        f"<li class='flex items-start gap-3 py-2'>"
        f"<span class='mt-1.5 w-2 h-2 rounded-full {dot_cls} flex-shrink-0'></span>"
        f"<span class='text-sm {text_cls}'>{icon} {texto}</span>"
        f"</li>"
    )


def build_html():
    sd = kpis["status_dist"]
    total = kpis["total_personas"]

    # ── Sección 0: KPIs + Insights Clave ──
    def kpi_card(label, value, sub="", highlight=False):
        bg = "bg-white border border-slate-100 shadow-sm shadow-slate-100/70 hover:shadow-md transition-all duration-200"
        return (
            f'<div class="{bg} rounded-xl px-5 py-4">'
            f'<p class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">{label}</p>'
            f'<p class="text-2xl font-bold text-slate-900">{value}</p>'
            + (f'<p class="text-xs text-slate-400 mt-0.5">{sub}</p>' if sub else "")
            + "</div>"
        )

    cards = (
        kpi_card("Total", str(total))
        + kpi_card("% Global", f"{kpis['pct_asistencia_global']}%")
        + kpi_card("Fieles", str(sd.get("Fiel", 0)), f"{fp(pct(sd.get('Fiel',0), total))}%")
        + kpi_card("Activos", str(sd.get("Activo", 0)), f"{fp(pct(sd.get('Activo',0), total))}%")
        + kpi_card("Inconstantes", str(sd.get("Inconstante", 0)), f"{fp(pct(sd.get('Inconstante',0), total))}%")
        + kpi_card("Inactivos", str(sd.get("Inactivo", 0)), f"{fp(pct(sd.get('Inactivo',0), total))}%")
        + kpi_card("En Riesgo", str(kpis["total_at_risk"]), f"{fp(pct(kpis['total_at_risk'], total))}%")
    )

    insights_list = "".join(insight_bullet(t, txt) for t, txt in key_insights)
    insights_block = f"""
<div class="bg-indigo-50 border border-indigo-100 rounded-2xl p-5 mt-6">
  <p class="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-3">Insights Clave del Ciclo</p>
  <ul class="divide-y divide-indigo-100/60">{insights_list}</ul>
</div>"""

    sec0 = section("KPIs Globales e Insights Clave", "0",
                   f'<div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">{cards}</div>'
                   + insights_block)

    # ── Sección 1: Semáforo ──
    rows1 = "".join(
        f"<tr class='hover:bg-slate-50 transition-all duration-200 {row_tint(g['delta'])}'>"
        f"{td(nombre, 'font-medium text-slate-900')}"
        f"{td(g['tipo'])}"
        f"{td(str(g['miembros']), 'text-center')}"
        f"<td class='px-6 py-4 text-sm font-semibold text-slate-700'>{fp(g['pct_global'])}%</td>"
        f"{td(fp(g['pct_q1'])+'%')}"
        f"{td(fp(g['pct_q2'])+'%')}"
        f"<td class='px-6 py-4'>{delta_badge(g['delta'])}</td>"
        + td(str(g['at_risk']) + " (" + fp(g['at_risk_pct']) + "%)", 'text-center')
        + "</tr>"
        for nombre, g in grupos_sorted
    )
    table1 = (
        f'<div class="overflow-x-auto"><table class="w-full">'
        f'<thead class="bg-slate-50/75"><tr>{"".join(th(h) for h in ["Grupo","Tipo","N","% Global","Q1%","Q2%","Δ Q1→Q2","En Riesgo"])}</tr></thead>'
        f'<tbody class="divide-y divide-slate-100">{rows1}</tbody></table></div>'
    )
    sec1 = section("Semáforo de Grupos", "1", table1)

    # ── Sección 2: Momentum ──
    mom_summary = (
        f'<div class="grid grid-cols-3 gap-4 mb-6">'
        f'<div class="bg-emerald-50 rounded-xl px-4 py-4 text-center"><p class="text-xs text-emerald-600 font-semibold uppercase tracking-wider mb-1">Mejoraron</p><p class="text-3xl font-bold text-emerald-700">{mejoras}</p><p class="text-xs text-emerald-600 mt-1">{fp(pct(mejoras, total_momentum))}%</p></div>'
        f'<div class="bg-slate-100 rounded-xl px-4 py-4 text-center"><p class="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-1">Se mantuvieron</p><p class="text-3xl font-bold text-slate-700">{estables}</p><p class="text-xs text-slate-500 mt-1">{fp(pct(estables, total_momentum))}%</p></div>'
        f'<div class="bg-rose-50 rounded-xl px-4 py-4 text-center"><p class="text-xs text-rose-600 font-semibold uppercase tracking-wider mb-1">Cayeron</p><p class="text-3xl font-bold text-rose-700">{caidas}</p><p class="text-xs text-rose-600 mt-1">{fp(pct(caidas, total_momentum))}%</p></div>'
        f'</div>'
    )
    rows2 = "".join(
        f"<tr class='hover:bg-slate-50 transition-colors'>"
        f"<td class='px-6 py-4 text-sm font-semibold text-slate-700 bg-slate-50/50'>Q1: {s1}</td>"
        + "".join(
            f"<td class='px-6 py-4 text-sm text-center font-medium "
            f"{'text-emerald-700 bg-emerald-50/50' if s1==s2 else 'text-slate-600'}'>"
            f"{momentum.get((s1,s2),0)}</td>"
            for s2 in STATUS_ORDER
        ) + "</tr>"
        for s1 in STATUS_ORDER
    )
    q1_header = '<th class="px-6 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Q1 \\ Q2</th>'
    matrix2 = (
        f'<div class="overflow-x-auto"><table class="w-full">'
        f'<thead class="bg-slate-50/75"><tr>{q1_header}{"".join(th(s) for s in STATUS_ORDER)}</tr></thead>'
        f'<tbody class="divide-y divide-slate-100">{rows2}</tbody></table></div>'
    )
    sec2 = section("Momentum Individual Q1→Q2", "2", mom_summary + matrix2)

    # ── Sección 3: Columna Vertebral ──
    rows3 = "".join(
        f"<tr class='hover:bg-slate-50 transition-colors'>"
        f"<td class='px-6 py-4 text-sm font-bold text-slate-400'>{i}</td>"
        f"{td(b['nombre'],'font-medium text-slate-900')}{td(b['grupo'])}"
        f"<td class='px-6 py-4 text-sm font-bold text-emerald-700'>{fp(b['pct'])}%</td>"
        f"<td class='px-6 py-4 text-sm text-slate-600'>{fp(b['pct_q1'])}%</td>"
        f"<td class='px-6 py-4 text-sm text-slate-600'>{fp(b['pct_q2'])}%</td>"
        f"<td class='px-6 py-4 text-sm font-semibold text-indigo-600'>+{b['racha']}</td></tr>"
        for i, b in enumerate(backbone, 1)
    )
    table3 = (
        f'<p class="text-xs text-slate-400 mb-4">Top 15 personas (excluyendo Mentores y Comentores)</p>'
        f'<div class="overflow-x-auto"><table class="w-full">'
        f'<thead class="bg-slate-50/75"><tr>{"".join(th(h) for h in ["#","Persona","Grupo","% Total","Q1%","Q2%","Racha"])}</tr></thead>'
        f'<tbody class="divide-y divide-slate-100">{rows3}</tbody></table></div>'
    )
    sec3 = section("Columna Vertebral — Top 15 (excluye Mentores y Comentores)", "3", table3)

    # ── Sección 4: Alertas Críticas ──
    total_criticos = sum(len(v) for v in criticos.values())
    criticos_html = f"<p class='text-xs text-slate-400 mb-4'>Total: {total_criticos} personas en {len(criticos)} grupos</p>"
    for gname in sorted(criticos.keys()):
        lista = criticos[gname]
        criticos_html += f"<p class='text-sm font-semibold text-slate-700 mt-4 mb-2'>{gname} <span class='text-rose-500'>({len(lista)})</span></p><ul class='space-y-1'>"
        for c in lista:
            criticos_html += (
                f"<li class='text-sm text-slate-600 flex items-center gap-2'>"
                f"<span class='w-2 h-2 rounded-full bg-rose-400 flex-shrink-0'></span>"
                f"{c['nombre']} — racha <span class='font-semibold text-rose-600'>{c['racha']}</span> — {fp(c['pct'])}%</li>"
            )
        criticos_html += "</ul>"
    sec4 = section("Alertas Críticas (racha ≤ -4)", "4", criticos_html)

    # ── Sección 5: Impacto de Eventos ──
    rows5 = "".join(
        f"<tr class='hover:bg-slate-50 transition-colors'>{td(fv)}"
        f"<td class='px-6 py-4 text-sm font-medium text-amber-700'>{ev}</td>"
        f"<td class='px-6 py-4 text-sm font-bold text-slate-700'>{fp(pev)}%</td>"
        f"<td class='px-6 py-4'>{delta_badge(round(pev - avg_normal, 1) if avg_normal else None)}</td>"
        f"{td(str(a) + '/' + str(t))}</tr>"
        for fv, ev, pev, a, t in sorted(event_pcts)
    )
    avg_note = f"<p class='text-xs text-slate-400 mb-4'>Promedio sesiones normales: <span class='font-semibold text-slate-600'>{fp(avg_normal)}%</span></p>"
    table5 = (
        avg_note
        + f'<div class="overflow-x-auto"><table class="w-full">'
        + f'<thead class="bg-slate-50/75"><tr>{"".join(th(h) for h in ["Fecha","Evento","% Asistencia","Δ vs Normal","Presentes"])}</tr></thead>'
        + f'<tbody class="divide-y divide-slate-100">{rows5}</tbody></table></div>'
    )
    sec5 = section("Impacto de Eventos", "5", table5)

    # ── Sección 6: Sesiones más Débiles ──
    rows6 = "".join(
        f"<tr class='hover:bg-slate-50 transition-colors'>{td(fv)}"
        f"<td class='px-6 py-4 text-sm font-bold text-rose-600'>{fp(pv)}%</td>"
        f"{td(str(a) + '/' + str(t))}</tr>"
        for fv, pv, a, t in sesiones_debiles
    )
    table6 = (
        f'<div class="overflow-x-auto"><table class="w-full">'
        f'<thead class="bg-slate-50/75"><tr>{"".join(th(h) for h in ["Fecha","% Asistencia","Presentes"])}</tr></thead>'
        f'<tbody class="divide-y divide-slate-100">{rows6}</tbody></table></div>'
    )
    sec6 = section("Sesiones más Débiles (sin eventos)", "6", table6)

    # ── Sección 7: Análisis por Rol ──
    rows7 = "".join(
        f"<tr class='hover:bg-slate-50 transition-colors'>{td(rn, 'font-medium')}{td(str(rv['n']),'text-center')}"
        f"<td class='px-6 py-4 text-sm font-bold text-slate-700'>{fp(pct(rv['asist'],rv['total']))}%</td></tr>"
        for rn, rv in roles_sorted
    )
    alerta_html = ""
    if mentores_alerta:
        alerta_html = f"<p class='text-sm font-semibold text-rose-600 mt-5 mb-2'>Mentores/Comentores con &lt; 60% asistencia ({len(mentores_alerta)})</p><ul class='space-y-1'>"
        for m in mentores_alerta:
            alerta_html += (
                f"<li class='text-sm text-slate-600'><span class='font-medium text-slate-800'>{m['nombre']}</span>"
                f" ({m['rol']}) — {m['grupo']} — <span class='font-semibold text-rose-600'>{fp(m['pct'])}%</span> — racha {m['racha']}</li>"
            )
        alerta_html += "</ul>"
    table7 = (
        f'<div class="overflow-x-auto"><table class="w-full">'
        f'<thead class="bg-slate-50/75"><tr>{"".join(th(h) for h in ["Rol","N","% Asistencia"])}</tr></thead>'
        f'<tbody class="divide-y divide-slate-100">{rows7}</tbody></table></div>{alerta_html}'
    )
    sec7 = section("Análisis por Rol", "7", table7)

    # ── Sección 8: Nuevos Ingresos ──
    rows8 = "".join(
        f"<tr class='hover:bg-slate-50 transition-colors'>{td(n['nombre'],'font-medium')}{td(n['grupo'])}{td(n['fecha_ingreso'])}"
        f"<td class='px-6 py-4 text-sm font-bold text-slate-700'>{fp(n['pct_q2'])}%</td>"
        f"{td(n['status_q2'])}"
        + risk_cell(n['at_risk'])
        + racha_cell(n['racha'])
        + "</tr>"
        for n in nuevos
    )
    table8 = (
        f'<p class="text-xs text-slate-400 mb-4">Total: {len(nuevos)} personas</p>'
        f'<div class="overflow-x-auto"><table class="w-full">'
        f'<thead class="bg-slate-50/75"><tr>{"".join(th(h) for h in ["Persona","Grupo","Ingreso","Q2%","Status Q2","En Riesgo","Racha"])}</tr></thead>'
        f'<tbody class="divide-y divide-slate-100">{rows8}</tbody></table></div>'
    )

    # Resumen nuevos ingresos
    if ni_buen_arranque:
        buenos_str = ", ".join(n["nombre"] for n in ni_buen_arranque)
    else:
        buenos_str = "Ninguno aún supera el 70%"

    if ni_seguimiento:
        seg_items = "".join(
            f"<li class='text-sm text-slate-600 flex items-start gap-2'>"
            f"<span class='mt-1.5 w-2 h-2 rounded-full bg-rose-400 flex-shrink-0'></span>"
            f"{n['nombre']} ({n['grupo']}) — Q2: {fp(n['pct_q2'])}%, racha {n['racha']}</li>"
            for n in ni_seguimiento
        )
        seg_block = f"<ul class='mt-2 space-y-1'>{seg_items}</ul>"
    else:
        seg_block = "<p class='text-sm text-slate-400 mt-1'>Ninguno</p>"

    if len(ni_en_riesgo) == 0 and ni_prom_q2 >= 60:
        diagnostico = f"Los nuevos ingresos muestran un arranque sólido. Ninguno está en riesgo y el promedio Q2 de {fp(ni_prom_q2)}% es alentador."
        diag_cls = "bg-emerald-50 border-emerald-100 text-emerald-800"
    elif ni_seguimiento and len(ni_en_riesgo) > len(nuevos) / 2:
        diagnostico = f"Más de la mitad de los nuevos ingresos ya están en riesgo. Se recomienda seguimiento pastoral activo en las próximas semanas."
        diag_cls = "bg-rose-50 border-rose-100 text-rose-800"
    else:
        diagnostico = f"Arranque mixto: {len(ni_buen_arranque)} con buen ritmo, {len(ni_en_riesgo)} en riesgo. Priorizar acompañamiento de quienes aún no se consolidan."
        diag_cls = "bg-amber-50 border-amber-100 text-amber-800"

    # Cards de En Riesgo: cada persona con su Q2% y racha
    riesgo_cards = "".join(
        f'<div class="bg-rose-50 border border-rose-100 rounded-xl px-3 py-3">'
        f'<p class="text-xs font-semibold text-rose-800 leading-tight">{n["nombre"]}</p>'
        f'<p class="text-xs text-rose-500 mt-0.5">{n["grupo"]}</p>'
        f'<div class="flex gap-2 mt-2">'
        f'<span class="text-xs bg-rose-100 text-rose-700 rounded px-1.5 py-0.5 font-medium">Q2: {fp(n["pct_q2"])}%</span>'
        f'<span class="text-xs bg-rose-100 text-rose-700 rounded px-1.5 py-0.5 font-medium">racha {n["racha"]}</span>'
        f'</div></div>'
        for n in ni_en_riesgo
    ) if ni_en_riesgo else "<p class='text-sm text-slate-400'>Ninguno en riesgo</p>"

    # Cards de Buen Arranque: cada persona con su Q2%
    arranque_cards = "".join(
        f'<div class="bg-emerald-50 border border-emerald-100 rounded-xl px-3 py-3">'
        f'<p class="text-xs font-semibold text-emerald-800 leading-tight">{n["nombre"]}</p>'
        f'<p class="text-xs text-emerald-500 mt-0.5">{n["grupo"]}</p>'
        f'<div class="flex gap-2 mt-2">'
        f'<span class="text-xs bg-emerald-100 text-emerald-700 rounded px-1.5 py-0.5 font-medium">Q2: {fp(n["pct_q2"])}%</span>'
        f'<span class="text-xs bg-emerald-100 text-emerald-700 rounded px-1.5 py-0.5 font-medium">racha +{n["racha"]}</span>'
        f'</div></div>'
        for n in ni_buen_arranque
    ) if ni_buen_arranque else "<p class='text-sm text-slate-400'>Ninguno aún supera el 70%</p>"

    resumen8 = f"""
<div class="mt-6 bg-amber-50 border border-amber-100 rounded-2xl p-5">
  <p class="text-xs font-semibold uppercase tracking-wider text-amber-500 mb-4">Seguimiento Nuevos Ingresos</p>

  <!-- KPIs summary -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
    <div class="bg-white rounded-xl px-4 py-3 text-center shadow-sm">
      <p class="text-xs text-slate-400 uppercase tracking-wider mb-1">Total</p>
      <p class="text-2xl font-bold text-slate-900">{len(nuevos)}</p>
    </div>
    <div class="bg-white rounded-xl px-4 py-3 text-center shadow-sm">
      <p class="text-xs text-slate-400 uppercase tracking-wider mb-1">Prom. Q2</p>
      <p class="text-2xl font-bold text-slate-900">{fp(ni_prom_q2)}%</p>
    </div>
    <div class="bg-rose-50 border border-rose-100 rounded-xl px-4 py-3 text-center">
      <p class="text-xs text-rose-400 uppercase tracking-wider mb-1">En Riesgo</p>
      <p class="text-2xl font-bold text-rose-600">{len(ni_en_riesgo)}</p>
      <p class="text-xs text-rose-400 mt-0.5">{fp(pct(len(ni_en_riesgo), len(nuevos)))}% del total</p>
    </div>
    <div class="bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3 text-center">
      <p class="text-xs text-emerald-500 uppercase tracking-wider mb-1">Buen Arranque</p>
      <p class="text-2xl font-bold text-emerald-600">{len(ni_buen_arranque)}</p>
      <p class="text-xs text-emerald-400 mt-0.5">Q2 &ge; 70%</p>
    </div>
  </div>

  <!-- En Riesgo desglosado -->
  <div class="mb-5">
    <p class="text-xs font-semibold text-rose-600 uppercase tracking-wider mb-3">&#9888; En Riesgo ({len(ni_en_riesgo)})</p>
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">{riesgo_cards}</div>
  </div>

  <!-- Buen Arranque desglosado -->
  <div class="mb-5">
    <p class="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-3">&#10003; Buen Arranque ({len(ni_buen_arranque)})</p>
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">{arranque_cards}</div>
  </div>

  <!-- En proceso (ni en riesgo ni buen arranque) -->
  <div class="mb-5">
    <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">En proceso ({len(ni_medio)})</p>
    <ul class="space-y-1">{"".join(f'<li class="flex items-center gap-2 text-sm text-slate-600"><span class="w-2 h-2 rounded-full bg-slate-400 flex-shrink-0"></span>{n["nombre"]} ({n["grupo"]}) — Q2: {fp(n["pct_q2"])}%, racha {n["racha"]}</li>' for n in ni_medio) if ni_medio else "<li class='text-sm text-slate-400'>Ninguno</li>"}</ul>
  </div>

  <!-- Diagnóstico -->
  <div class="p-3 rounded-xl border {diag_cls}">
    <p class="text-xs font-semibold uppercase tracking-wider mb-1 opacity-70">Diagnóstico</p>
    <p class="text-sm">{diagnostico}</p>
  </div>
</div>"""

    sec8 = section("Nuevos Ingresos (FECHA_INGRESO)", "8", table8 + resumen8)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Insights Report — J1 Asistencia {fecha_reporte}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="bg-slate-50 min-h-screen">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

    <div class="mb-8 flex items-center gap-4">
      <div class="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center flex-shrink-0">
        <span class="text-white font-bold text-sm">J1</span>
      </div>
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900">Insights Report — J1 Alianza de Monterrico</h1>
        <p class="text-sm text-slate-400 mt-0.5">Análisis profundo · {fecha_reporte}</p>
      </div>
    </div>

    {sec0}{sec1}{sec2}{sec3}{sec4}{sec5}{sec6}{sec7}{sec8}

  </div>
</body>
</html>"""
    return html


# ── Escribir outputs ─────────────────────────────────────────────────────────
md_content = build_md()
html_content = build_html()

OUT_MD.write_text(md_content, encoding="utf-8")
OUT_HTML.write_text(html_content, encoding="utf-8")

md_kb = OUT_MD.stat().st_size / 1024
html_kb = OUT_HTML.stat().st_size / 1024
print(f"[OK] insights generado en subagents/sub_insights/reports/")
print(f"     {OUT_MD.name}: {md_kb:.1f} KB")
print(f"     {OUT_HTML.name}: {html_kb:.1f} KB")

os.startfile(str(OUT_HTML))
