"""
Tool: generate_dashboard.py
Genera el dashboard interactivo — Tailwind CSS + ApexCharts + Dark mode
Lee .tmp/asistencia_processed.json → escribe .tmp/dashboard.html
"""
import json
import os
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"
OUTPUT_PATH = TMP_DIR / "dashboard.html"


def main():
    processed_path = TMP_DIR / "asistencia_processed.json"
    if not processed_path.exists():
        print("[ERROR] .tmp/asistencia_processed.json no encontrado.")
        sys.exit(1)

    with open(processed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data_json = json.dumps(data, ensure_ascii=False)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(build_html(data_json))

    print(f"[OK] dashboard.html generado en: {OUTPUT_PATH}")
    if not os.getenv("CI"):
        print("[...] Abriendo en el browser...")
        webbrowser.open(OUTPUT_PATH.as_uri())


def build_html(data_json: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>J1 · Alianza de Monterrico</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config = {{ darkMode:'class', theme:{{ extend:{{ fontFamily:{{ sans:['Inter','system-ui','sans-serif'] }} }} }} }}</script>
<script src="https://cdn.jsdelivr.net/npm/apexcharts@3.45.2/dist/apexcharts.min.js"></script>
<style>
/* ── Color tokens ─────────────────────────────── */
:root {{
  --bg:#F8FAFC; --surface:#FFFFFF; --surface2:#F1F5F9;
  --border:#E2E8F0; --text:#0F172A; --muted:#64748B; --hover:#EEF2FF;
}}
.dark {{
  --bg:#0F172A; --surface:#1E293B; --surface2:#0F172A;
  --border:#334155; --text:#F8FAFC; --muted:#94A3B8; --hover:#1E2D4A;
}}
body {{ font-family:'Inter',system-ui,sans-serif; background:var(--bg); color:var(--text); }}

/* ── Pages ───────────── */
.page {{ display:none; }} .page.active {{ display:block; }}

/* ── Scrollbar ───────── */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:#CBD5E1; border-radius:4px; }}
.dark ::-webkit-scrollbar-thumb {{ background:#475569; }}

/* ── Modal ───────────── */
.modal-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:1000; align-items:center; justify-content:center; }}
.modal-overlay.open {{ display:flex; }}
.modal-box {{ background:var(--surface); border-radius:20px; width:740px; max-width:95vw; max-height:90vh; overflow-y:auto; padding:28px; position:relative; box-shadow:0 25px 50px rgba(0,0,0,.25); }}

/* ── Tabs ───────────────────────── */
.tab-btn {{ display:flex; align-items:center; gap:6px; padding:8px 18px; border-radius:10px; font-size:14px; font-weight:500; color:var(--muted); transition:all .15s; cursor:pointer; border:none; background:transparent; white-space:nowrap; }}
.tab-btn.active {{ background:var(--surface); color:#4F46E5; box-shadow:0 1px 4px rgba(0,0,0,.12); }}
.tab-btn:hover:not(.active) {{ background:var(--surface2); color:var(--text); }}

/* ── Card ────────────── */
.card {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.card-title {{ font-size:14px; font-weight:600; color:var(--text); margin-bottom:16px; }}

/* ── KPI Card ─────────── */
.kpi-card {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:20px; transition:all .15s; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.kpi-card.clickable {{ cursor:pointer; }}
.kpi-card.clickable:hover {{ transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,.1); }}

/* ── Table ───────────── */
.tbl-wrap {{ overflow-x:auto; }}
.tbl {{ width:100%; border-collapse:collapse; }}
.tbl th {{ padding:10px 16px; text-align:left; font-size:11px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; border-bottom:1px solid var(--border); background:var(--surface2); white-space:nowrap; position:sticky; top:0; z-index:5; }}
.tbl th.sortable {{ cursor:pointer; user-select:none; }}
.tbl th.sortable:hover {{ color:#4F46E5; }}
.tbl th.sort-active {{ color:#4F46E5; }}
.sort-ind {{ font-size:10px; margin-left:3px; opacity:.5; }}
.sort-active .sort-ind {{ opacity:1; }}
.tbl td {{ padding:11px 16px; font-size:14px; border-bottom:1px solid var(--border); }}
.tbl tr:last-child td {{ border-bottom:none; }}
.tbl tr.clickable {{ cursor:pointer; transition:background .1s; }}
.tbl tr.clickable:hover {{ background:var(--hover); }}

/* ── Badge ───────────── */
.badge {{ display:inline-flex; align-items:center; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600; }}
.badge-fiel {{ background:#D1FAE5; color:#065F46; }}
.badge-activo {{ background:#EEF2FF; color:#3730A3; }}
.badge-inconstante {{ background:#FEF3C7; color:#92400E; }}
.badge-inactivo {{ background:#FEE2E2; color:#991B1B; }}
.badge-riesgo {{ background:#FEE2E2; color:#991B1B; }}

/* ── Progress bar ─────── */
.pct-wrap {{ display:flex; align-items:center; gap:8px; }}
.pct-bar {{ height:6px; border-radius:3px; flex:1; background:var(--border); overflow:hidden; min-width:60px; }}
.pct-bar-fill {{ height:100%; border-radius:3px; }}
.pct-text {{ font-size:13px; font-weight:600; min-width:38px; text-align:right; }}

/* ── Timeline ─────────── */
.tl-dot {{ width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:14px; position:relative; cursor:default; flex-direction:column; }}
.tl-dot.asistio {{ background:#D1FAE5; color:#065F46; }}
.tl-dot.falto {{ background:#FEE2E2; color:#991B1B; }}
.tl-dot.evento {{ background:#FEF3C7; border:2px solid #F59E0B; color:#92400E; }}
.tl-dot .tt {{ display:none; position:absolute; bottom:42px; left:50%; transform:translateX(-50%); background:#111; color:#fff; font-size:10px; padding:3px 8px; border-radius:4px; white-space:nowrap; z-index:20; pointer-events:none; }}
.tl-dot:hover .tt {{ display:block; }}
.tl-label {{ font-size:9px; margin-top:1px; opacity:.65; }}

/* ── Matrix ──────────── */
.matrix-table {{ border-collapse:collapse; font-size:13px; }}
.matrix-table th,.matrix-table td {{ padding:8px 14px; border:1px solid var(--border); text-align:center; }}
.matrix-table th {{ background:var(--surface2); font-weight:600; color:var(--text); }}
.m-same {{ background:var(--surface2); color:var(--muted); }}
.m-up {{ background:#D1FAE5; color:#065F46; font-weight:700; }}
.m-down {{ background:#FEE2E2; color:#991B1B; font-weight:700; }}
.m-zero {{ color:var(--border); }}

/* ── Alert strip ──────── */
.alert-strip {{ background:#FEF2F2; border:1px solid #FECACA; border-radius:10px; padding:12px 16px; font-size:13px; color:#991B1B; display:flex; align-items:center; gap:8px; }}
.dark .alert-strip {{ background:#450a0a; border-color:#7f1d1d; color:#fca5a5; }}

/* ── Mini table (modal) ─ */
.mini-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
.mini-table th {{ padding:8px 12px; border-bottom:1px solid var(--border); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.4px; color:var(--muted); background:var(--surface2); }}
.mini-table td {{ padding:9px 12px; border-bottom:1px solid var(--border); }}
.mini-table tr:last-child td {{ border-bottom:none; }}
.mini-table tr.clickable {{ cursor:pointer; }}
.mini-table tr.clickable:hover {{ background:var(--hover); }}

/* ── Modal stats ──────── */
.modal-stat {{ background:var(--surface2); border-radius:10px; padding:14px; text-align:center; }}
.modal-stat-val {{ font-size:22px; font-weight:800; }}
.modal-stat-lbl {{ font-size:11px; color:var(--muted); margin-top:3px; }}
.racha-badge {{ display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:8px; font-size:13px; font-weight:600; margin-bottom:16px; }}
.racha-pos {{ background:#D1FAE5; color:#065F46; }}
.racha-neg {{ background:#FEE2E2; color:#991B1B; }}

/* ── Form controls ─────── */
.ctrl {{ padding:7px 12px; border:1px solid var(--border); border-radius:8px; font-size:13px; background:var(--surface); color:var(--text); cursor:pointer; outline:none; }}
.ctrl:focus {{ border-color:#4F46E5; }}
.btn-sec {{ padding:7px 12px; border:1px solid var(--border); border-radius:8px; font-size:12px; font-weight:500; background:var(--surface); color:var(--text); cursor:pointer; display:inline-flex; align-items:center; gap:5px; }}
.btn-sec:hover {{ background:var(--surface2); }}

/* ── Responsive ────────── */
@media(max-width:900px) {{ .charts-2col {{ grid-template-columns:1fr !important; }} }}
@media(max-width:640px) {{
  .tab-text {{ display:none; }}
  .kpi-inner {{ grid-template-columns:repeat(2,1fr) !important; }}
  thead {{ display:none; }}
  tbody {{ display:block; padding:8px; }}
  tr.clickable {{ display:block; border-radius:10px; border:1px solid var(--border); margin-bottom:10px; overflow:hidden; background:var(--surface); }}
  tr.clickable td {{ display:flex; justify-content:space-between; align-items:center; padding:9px 12px; border-bottom:1px solid var(--border); font-size:13px; }}
  tr.clickable td:last-child {{ border-bottom:none; }}
  tr.clickable td[data-label]::before {{ content:attr(data-label); font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.4px; flex-shrink:0; min-width:72px; margin-right:8px; }}
  .modal-overlay {{ align-items:flex-end; }}
  .modal-box {{ border-radius:16px 16px 0 0; max-height:88vh; width:100%; max-width:100vw; padding:18px; }}
  .filters-row {{ flex-wrap:nowrap; overflow-x:auto; padding-bottom:2px; }}
}}
</style>
</head>
<body class="min-h-screen">

<!-- ══════════════════ HEADER ══════════════════ -->
<header class="sticky top-0 z-50 shadow-sm" style="background:var(--surface);border-bottom:1px solid var(--border)">
  <div class="max-w-screen-xl mx-auto px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-xl bg-slate-900 flex items-center justify-center flex-shrink-0">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
      </div>
      <div>
        <h1 class="text-[15px] font-bold leading-none" style="color:var(--text)">J1 · Alianza de Monterrico</h1>
        <p class="text-[11px] mt-0.5" style="color:var(--muted)">Reporte de Asistencia Semanal</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <span id="lastUpdated" class="text-[11px] hidden sm:block" style="color:var(--muted)"></span>
      <button onclick="toggleDark()" class="p-2 rounded-lg transition-colors" style="background:var(--surface2);color:var(--muted)" title="Cambiar tema">
        <svg id="iconSun" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        <svg id="iconMoon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
      </button>
    </div>
  </div>
</header>

<!-- ══════════════════ MAIN ══════════════════ -->
<main class="max-w-screen-xl mx-auto px-6 py-6">

  <!-- Tabs -->
  <div class="flex gap-1 p-1 rounded-xl w-fit mb-6" style="background:var(--surface2)">
    <button class="tab-btn active" data-page="overview" onclick="showPage('overview',this)">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
      <span class="tab-text">Resumen</span>
    </button>
    <button class="tab-btn" data-page="grupos" onclick="showPage('grupos',this)">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
      <span class="tab-text">Grupos</span>
    </button>
    <button class="tab-btn" data-page="personas" onclick="showPage('personas',this)">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      <span class="tab-text">Personas</span>
    </button>
    <button class="tab-btn" data-page="riesgo" onclick="showPage('riesgo',this)">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
      <span class="tab-text">Riesgo</span>
    </button>
  </div>

  <!-- ══ PAGE: RESUMEN ══ -->
  <div class="page active" id="page-overview">
    <div id="kpiGrid" class="grid gap-4 mb-6 kpi-inner" style="grid-template-columns:repeat(7,1fr)"></div>
    <div class="grid gap-5 mb-6 charts-2col" style="grid-template-columns:1fr 1fr">

      <!-- Ranking de grupos -->
      <div class="card p-5">
        <div class="card-title">Ranking de grupos por % de asistencia</div>
        <p style="font-size:12px;color:var(--muted);margin-top:-10px;margin-bottom:14px">Porcentaje de asistencia sobre el total</p>
        <div id="rankingPromLabel" style="font-size:11px;color:#4F46E5;font-weight:600;margin-bottom:12px"></div>
        <div id="rankingGrupos" style="overflow-y:auto;max-height:360px;padding-right:4px"></div>
      </div>

      <!-- Donut + Stats list -->
      <div class="card p-5" style="display:flex;flex-direction:column">
        <div class="card-title">Distribución por tipo de grupo</div>
        <p style="font-size:12px;color:var(--muted);margin-top:-10px;margin-bottom:14px">Participación porcentual y cantidad de personas</p>
        <div style="display:flex;align-items:center;gap:24px;flex:1">
          <div style="width:55%;flex-shrink:0;position:relative">
            <div id="chartTipos"></div>
            <div id="donutCenter" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none;line-height:1">
              <div id="donutTotal" style="font-size:28px;font-weight:800;color:var(--text)"></div>
              <div style="font-size:12px;color:#64748B;margin-top:4px">personas</div>
            </div>
          </div>
          <div id="tiposStats" style="flex:1;display:flex;flex-direction:column;gap:16px"></div>
        </div>
      </div>

      <!-- Evolución semanal -->
      <div class="card p-5" style="grid-column:1/-1">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
          <div>
            <div class="card-title" style="margin-bottom:0">Evolución Semanal — % Asistencia</div>
            <div style="font-size:12px;color:var(--muted);margin-top:2px">Puntos naranjos = eventos especiales</div>
          </div>
          <div id="evolPromLabel" style="display:flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:#94A3B8">
            <svg width="20" height="8" viewBox="0 0 20 2"><line x1="0" y1="1" x2="20" y2="1" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="4 3"/></svg>
            <span></span>
          </div>
        </div>
        <div id="chartEvolucion" style="height:280px"></div>
        <div id="evolStats"></div>
      </div>

    </div>
  </div>

  <!-- ══ PAGE: GRUPOS ══ -->
  <div class="page" id="page-grupos">
    <div class="card p-5 mb-5">
      <div class="card-title">Comparativa Q1 vs Q2 por Grupo</div>
      <div id="chartQ1Q2" style="height:320px"></div>
    </div>
    <div class="card mb-5" style="overflow:hidden">
      <div class="flex items-center justify-between flex-wrap gap-3 p-4" style="border-bottom:1px solid var(--border)">
        <span class="text-sm font-semibold">Detalle por Grupo <span class="text-xs font-normal" style="color:var(--muted)">(click para ver detalle)</span></span>
        <div class="flex gap-2 items-center filters-row">
          <select class="ctrl" id="filterGrupoTipo" onchange="renderTableGrupos()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option><option value="GDA">GDA</option><option value="GDC">GDC</option>
          </select>
          <select class="ctrl" id="filterGrupoQ" onchange="renderTableGrupos()">
            <option value="total">Total</option><option value="q1">Q1</option><option value="q2">Q2</option>
          </select>
          <button class="btn-sec" onclick="exportCSV('grupos')">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            CSV
          </button>
        </div>
      </div>
      <div class="tbl-wrap">
        <table class="tbl">
          <thead><tr>
            <th class="sortable" id="th-g-nombre" onclick="sortGrupos('nombre')">Grupo <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-g-tipo" onclick="sortGrupos('tipo_grupo')">Tipo <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-g-miembros" onclick="sortGrupos('num_miembros')">Personas <span class="sort-ind">↕</span></th>
            <th>Sesiones</th>
            <th class="sortable" id="th-g-pct" onclick="sortGrupos('pct_asistencia')">% Asistencia <span class="sort-ind">↕</span></th>
            <th>Formales</th>
            <th class="sortable" id="th-g-mem" onclick="sortGrupos('pct_membresia')">% Memb. <span class="sort-ind">↕</span></th>
            <th>Fieles</th><th>Activos</th><th>Inconst.</th><th>Inactivos</th>
          </tr></thead>
          <tbody id="tbodyGrupos"></tbody>
        </table>
      </div>
    </div>
    <div class="card" style="overflow:hidden">
      <div class="flex items-center justify-between flex-wrap gap-3 p-4" style="border-bottom:1px solid var(--border)">
        <span class="text-sm font-semibold">Cambios de Status Q1 → Q2</span>
        <div class="flex gap-2 items-center">
          <select class="ctrl" id="filterMatrixTipo" onchange="updateMatrixGrupos();renderMatrix()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option><option value="GDA">GDA</option><option value="GDC">GDC</option>
          </select>
          <select class="ctrl" id="filterMatrixGrupo" onchange="renderMatrix()">
            <option value="">Todos los grupos</option>
          </select>
        </div>
      </div>
      <div class="p-5 overflow-x-auto">
        <table class="matrix-table" id="matrixTable"></table>
      </div>
    </div>
  </div>

  <!-- ══ PAGE: RIESGO ══ -->
  <div class="page" id="page-riesgo">
    <div class="alert-strip mb-5">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
      <span>Personas con <strong>0 asistencias en las últimas 4 sesiones de su grupo</strong>. Requieren seguimiento.</span>
    </div>
    <div class="grid gap-4 mb-5" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr))">
      <div class="kpi-card">
        <div class="text-xs font-semibold uppercase tracking-wider mb-3" style="color:var(--muted)">Total en riesgo</div>
        <div class="text-3xl font-extrabold" style="color:#DC2626" id="kpiRiesgo">-</div>
        <div class="text-xs mt-1" style="color:var(--muted)">de <span id="kpiTotal">-</span> participantes activos</div>
      </div>
    </div>
    <div class="card" style="overflow:hidden">
      <div class="flex items-center justify-between flex-wrap gap-3 p-4" style="border-bottom:1px solid var(--border)">
        <span class="text-sm font-semibold">Listado de personas en riesgo</span>
        <div class="flex gap-2 items-center filters-row">
          <select class="ctrl" id="filterRiesgoTipo" onchange="renderRiesgo()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option><option value="GDA">GDA</option><option value="GDC">GDC</option>
          </select>
          <button class="btn-sec" onclick="exportCSV('riesgo')">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            CSV
          </button>
        </div>
      </div>
      <div class="tbl-wrap">
        <table class="tbl">
          <thead><tr>
            <th class="sortable" id="th-r-nombre" onclick="sortRiesgo('nombre_completo')">Nombre <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-r-grupo" onclick="sortRiesgo('grupo_actual')">Grupo <span class="sort-ind">↕</span></th>
            <th>Tipo</th>
            <th class="sortable" id="th-r-pct" onclick="sortRiesgo('pct_total')">% Total <span class="sort-ind">↕</span></th>
            <th>Status</th>
            <th class="sortable" id="th-r-ultima" onclick="sortRiesgo('ultima_asistencia')">Última asistencia <span class="sort-ind">↕</span></th>
          </tr></thead>
          <tbody id="tbodyRiesgo"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ══ PAGE: PERSONAS ══ -->
  <div class="page" id="page-personas">
    <div class="card" style="overflow:hidden">
      <div class="flex items-center justify-between flex-wrap gap-3 p-4" style="border-bottom:1px solid var(--border)">
        <span class="text-sm font-semibold">Participantes</span>
        <div class="flex gap-2 items-center flex-wrap filters-row">
          <input class="ctrl" style="width:180px" id="searchPersona" placeholder="Buscar nombre..." oninput="renderPersonas()">
          <select class="ctrl" id="filterPGrupo" onchange="renderPersonas()"><option value="">Todos los grupos</option></select>
          <select class="ctrl" id="filterPTipo" onchange="renderPersonas()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option><option value="GDA">GDA</option><option value="GDC">GDC</option>
          </select>
          <select class="ctrl" id="filterPStatus" onchange="renderPersonas()">
            <option value="">Todos los status</option>
            <option>Fiel</option><option>Activo</option><option>Inconstante</option><option>Inactivo</option>
          </select>
          <button class="btn-sec" onclick="exportCSV('personas')">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            CSV
          </button>
        </div>
      </div>
      <div class="tbl-wrap">
        <table class="tbl">
          <thead><tr>
            <th class="sortable" id="th-p-nombre" onclick="sortPersonas('nombre_completo')">Nombre <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-p-grupo" onclick="sortPersonas('grupo_actual')">Grupo <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-p-tipo" onclick="sortPersonas('tipo_grupo')">Tipo <span class="sort-ind">↕</span></th>
            <th>Rol</th>
            <th class="sortable" id="th-p-q1" onclick="sortPersonas('pct_q1')">Q1% <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-p-q2" onclick="sortPersonas('pct_q2')">Q2% <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-p-total" onclick="sortPersonas('pct_total')">Total% <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-p-status" onclick="sortPersonas('status')">Status <span class="sort-ind">↕</span></th>
          </tr></thead>
          <tbody id="tbodyPersonas"></tbody>
        </table>
      </div>
    </div>
  </div>

</main>

<!-- ══════════════════ MODAL ══════════════════ -->
<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
  <div class="modal-box">
    <button onclick="closeModalDirect()" style="position:absolute;top:16px;right:16px;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);background:var(--surface2);color:var(--muted);cursor:pointer;">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
    </button>
    <div id="modalContent"></div>
  </div>
</div>

<script>
const DATA = {data_json};

// ── DARK MODE ─────────────────────────────────────────────────────────────
let chartTiposInst = null, chartEvolInst = null, chartQ1Q2Inst = null;

function isDark() {{ return document.documentElement.classList.contains('dark'); }}

function applyTheme(dark) {{
  document.documentElement.classList.toggle('dark', dark);
  document.getElementById('iconSun').style.display = dark ? 'block' : 'none';
  document.getElementById('iconMoon').style.display = dark ? 'none' : 'block';
  const mode = dark ? 'dark' : 'light';
  [chartTiposInst, chartEvolInst, chartQ1Q2Inst].forEach(c => {{
    if (c) c.updateOptions({{ theme: {{ mode }} }});
  }});
}}

function toggleDark() {{
  const dark = !isDark();
  localStorage.setItem('theme', dark ? 'dark' : 'light');
  applyTheme(dark);
}}

(function initTheme() {{
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const dark = saved === 'dark' || (!saved && prefersDark);
  if (dark) document.documentElement.classList.add('dark');
  document.getElementById('iconSun').style.display = dark ? 'block' : 'none';
  document.getElementById('iconMoon').style.display = dark ? 'none' : 'block';
}})();

// ── UTILS ─────────────────────────────────────────────────────────────────
function pctColor(p) {{ return p>=80?'#10B981':p>=51?'#4F46E5':p>0?'#F59E0B':'#EF4444'; }}
function badgeHtml(s) {{
  const m={{'Fiel':'fiel','Activo':'activo','Inconstante':'inconstante','Inactivo':'inactivo'}};
  return `<span class="badge badge-${{m[s]||'inactivo'}}">${{s}}</span>`;
}}
function pctBar(p) {{
  return `<div class="pct-wrap"><div class="pct-bar"><div class="pct-bar-fill" style="width:${{p}}%;background:${{pctColor(p)}}"></div></div><span class="pct-text" style="color:${{pctColor(p)}}">${{p}}%</span></div>`;
}}
function fmtDate(iso) {{ const [y,m,d]=iso.split('-'); return d+'/'+m; }}
function weeksAgo(isoDate) {{
  if(!isoDate) return 'Nunca';
  const ref = DATA.generated_at ? new Date(DATA.generated_at) : new Date();
  const days = Math.floor((ref-new Date(isoDate))/86400000);
  if(days<7) return 'Esta semana';
  const w = Math.floor(days/7);
  return w===1 ? 'Hace 1 semana' : `Hace ${{w}} semanas`;
}}
function baseChartOpts() {{
  return {{
    chart: {{ fontFamily:'Inter,system-ui,sans-serif', toolbar:{{ show:false }} }},
    theme: {{ mode: isDark()?'dark':'light' }},
    grid: {{ borderColor: isDark()?'#293548':'#EEF2FF', strokeDashArray:0 }},
  }};
}}

// ── NAVIGATION ────────────────────────────────────────────────────────────
function showPage(name, btn) {{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(t=>t.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  const target = btn || document.querySelector(`.tab-btn[data-page="${{name}}"]`);
  if(target) target.classList.add('active');
}}
function navToStatus(page, status) {{
  showPage(page);
  if(page==='personas'&&status) {{
    document.getElementById('filterPStatus').value=status;
    renderPersonas();
  }}
  if(page==='riesgo') {{}}
}}

// ── SORT ─────────────────────────────────────────────────────────────────
const KEY_TO_ID = {{
  nombre_completo:'nombre',grupo_actual:'grupo',tipo_grupo:'tipo',
  pct_total:'total',pct_q1:'q1',pct_q2:'q2',status:'status',
  pct_asistencia:'pct',num_miembros:'miembros',pct_membresia:'mem',
  ultima_asistencia:'ultima',nombre:'nombre',
}};
const sortState = {{
  personas:{{key:'pct_total',dir:-1}},
  grupos:{{key:'pct_asistencia',dir:-1}},
  riesgo:{{key:'grupo_actual',dir:1}},
}};
function applySortIndicators(prefix, state) {{
  document.querySelectorAll(`[id^="th-${{prefix}}-"]`).forEach(th=>{{
    th.classList.remove('sort-active');
    const si=th.querySelector('.sort-ind');if(si)si.textContent='↕';
  }});
  const th=document.getElementById(`th-${{prefix}}-${{KEY_TO_ID[state.key]||state.key}}`);
  if(th){{th.classList.add('sort-active');const si=th.querySelector('.sort-ind');if(si)si.textContent=state.dir>0?'↑':'↓';}}
}}
function sortBy(arr, key, dir) {{
  return [...arr].sort((a,b)=>{{
    let av=a[key],bv=b[key];
    if(av==null||av==='')return 1;if(bv==null||bv==='')return-1;
    if(typeof av==='number')return(av-bv)*dir;
    return String(av).localeCompare(String(bv),'es')*dir;
  }});
}}
function sortPersonas(key) {{
  sortState.personas.dir=(sortState.personas.key===key)?sortState.personas.dir*-1:(typeof DATA.personas[0][key]==='number'?-1:1);
  sortState.personas.key=key;renderPersonas();
}}
function sortGrupos(key) {{
  sortState.grupos.dir=(sortState.grupos.key===key)?sortState.grupos.dir*-1:(typeof DATA.grupos[0][key]==='number'?-1:1);
  sortState.grupos.key=key;renderTableGrupos();
}}
function sortRiesgo(key) {{
  const sample=(DATA.at_risk||[])[0]||{{}};
  sortState.riesgo.dir=(sortState.riesgo.key===key)?sortState.riesgo.dir*-1:(typeof sample[key]==='number'?-1:1);
  sortState.riesgo.key=key;renderRiesgo();
}}

// ── KPIs ──────────────────────────────────────────────────────────────────
function renderKPIs() {{
  const k=DATA.kpis,sd=k.status_dist||{{}};
  const ev=DATA.evolucion||[];
  let deltaHtml='';
  if(ev.length>=2) {{
    const d=parseFloat((ev[ev.length-1].pct-ev[ev.length-2].pct).toFixed(1));
    const col=d>0?'#10B981':d<0?'#EF4444':'#94A3B8';
    const arrow=d>0?'↑':d<0?'↓':'→';
    deltaHtml=`<div style="font-size:12px;font-weight:700;color:${{col}};margin-top:4px">${{arrow}} ${{d>0?'+':''}}${{d}}pp vs sem. ant.</div>`;
  }}
  const cards=[
    {{l:'Participantes',  v:k.total_personas,              sub:'con grupo activo',   col:'#4F46E5', icon:'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 8 0 4 4 0 0 0-8 0M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75', page:null}},
    {{l:'% Asistencia',   v:k.pct_asistencia_global+'%',   sub:'promedio general',   col:'#0EA5E9', icon:'M23 6L13.5 15.5 8.5 10.5 1 18M17 6h6v6', page:null, extra:deltaHtml}},
    {{l:'Fieles',         v:sd.Fiel||0,                    sub:'80%+',               col:'#10B981', icon:'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z', page:'personas',status:'Fiel'}},
    {{l:'Activos',        v:sd.Activo||0,                  sub:'51–79%',             col:'#4F46E5', icon:'M22 12h-4l-3 9L9 3l-3 9H2', page:'personas',status:'Activo'}},
    {{l:'Inconstantes',   v:sd.Inconstante||0,             sub:'1–50%',              col:'#F59E0B', icon:'M13 2L3 14h9l-1 8 10-12h-9l1-8z', page:'personas',status:'Inconstante'}},
    {{l:'Inactivos',      v:sd.Inactivo||0,                sub:'0%',                 col:'#EF4444', icon:'M16 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM1 21v-2a7 7 0 0 1 7-7h4M17 17l5 5M22 17l-5 5', page:'personas',status:'Inactivo'}},
    {{l:'En Riesgo',      v:k.total_at_risk||0,            sub:'0 asist. / 4 sem.',  col:'#DC2626', icon:'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01', page:'riesgo'}},
  ];
  document.getElementById('kpiGrid').innerHTML=cards.map(c=>{{
    const nav=c.page?`onclick="navToStatus('${{c.page}}','${{c.status||''}}')" tabindex="0"`:'';
    return`<div class="kpi-card${{c.page?' clickable':''}}" ${{nav}} style="border-left:4px solid ${{c.col}}">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)">${{c.l}}</span>
        <div style="padding:6px;border-radius:8px;background:${{c.col}}18">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="${{c.col}}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${{c.icon}}"></path></svg>
        </div>
      </div>
      <div style="font-size:28px;font-weight:800;color:${{c.col}};line-height:1">${{c.v}}</div>
      <div style="font-size:11px;color:var(--muted);margin-top:4px">${{c.sub}}</div>
      ${{c.extra||''}}
    </div>`;
  }}).join('');
  document.getElementById('kpiRiesgo').textContent=k.total_at_risk||0;
  document.getElementById('kpiTotal').textContent=k.total_personas;
}}

// ── CHARTS ────────────────────────────────────────────────────────────────
function renderRankingGrupos() {{
  const grupos = sortBy(DATA.grupos, 'pct_asistencia', -1);
  const avg = DATA.kpis.pct_asistencia_global;
  const medals = ['🥇','🥈','🥉'];
  document.getElementById('rankingPromLabel').innerHTML =
    `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#4F46E5;margin-right:5px;vertical-align:middle"></span>Promedio general: ${{avg}}%`;
  document.getElementById('rankingGrupos').innerHTML = grupos.map((g, i) => {{
    const pct = g.pct_asistencia;
    const above = pct >= avg;
    const barColor = above ? '#4F46E5' : '#CBD5E1';
    const pctColor2 = above ? '#4F46E5' : 'var(--muted)';
    const rank = i < 3
      ? `<span style="font-size:16px;line-height:1">${{medals[i]}}</span>`
      : `<span style="font-size:12px;font-weight:600;color:var(--muted);display:inline-block;width:20px;text-align:center">${{i+1}}</span>`;
    return `<div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border)">
      <div style="width:26px;text-align:center;flex-shrink:0">${{rank}}</div>
      <div style="width:150px;font-size:13px;font-weight:500;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--text)">${{g.nombre}}</div>
      <div style="flex:1;position:relative;height:7px;background:var(--border);border-radius:4px">
        <div style="height:100%;width:${{pct}}%;background:${{barColor}};border-radius:4px;transition:width .3s"></div>
        <div style="position:absolute;top:-4px;left:${{avg}}%;width:2px;height:15px;background:#4F46E5;border-radius:1px;opacity:0.5"></div>
      </div>
      <div style="width:40px;font-size:11px;font-weight:700;text-align:right;color:${{pctColor2}}">${{pct}}%</div>
    </div>`;
  }}).join('');
}}

function renderChartTipos() {{
  const t = DATA.tipos;
  const total = DATA.kpis.total_personas;
  const colors = ['#4F46E5','#10B981','#F59E0B'];
  chartTiposInst = new ApexCharts(document.getElementById('chartTipos'), {{
    ...baseChartOpts(),
    chart: {{ ...baseChartOpts().chart, type:'donut', height:260 }},
    series: t.map(x => x.personas),
    labels: t.map(x => x.tipo),
    colors,
    stroke: {{ width:0 }},
    dataLabels: {{ enabled:false }},
    plotOptions: {{ pie: {{ donut: {{
      size: '70%',
      labels: {{ show: false }}
    }} }} }},
    legend: {{ show: false }},
    tooltip: {{ y: {{ formatter: v => `${{v}} personas` }} }},
  }});
  chartTiposInst.render();
  // overlay del centro del donut
  const donutTotal = document.getElementById('donutTotal');
  if (donutTotal) donutTotal.textContent = total;
  // stats list a la derecha
  const statsEl = document.getElementById('tiposStats');
  if (statsEl) {{
    const maxTipo = t.reduce((a,b) => a.personas > b.personas ? a : b);
    const minTipo = t.reduce((a,b) => a.personas < b.personas ? a : b);
    const ratio = Math.round(maxTipo.personas / minTipo.personas);
    statsEl.innerHTML = t.map((item, i) => {{
      const pct = total > 0 ? Math.round(item.personas / total * 100) : 0;
      return `<div style="display:flex;align-items:center;gap:10px">
        <div style="width:10px;height:10px;border-radius:3px;background:${{colors[i]}};flex-shrink:0;margin-top:2px"></div>
        <div>
          <div style="font-size:22px;font-weight:800;color:${{colors[i]}};line-height:1">${{pct}}%</div>
          <div style="font-size:12px;font-weight:500;color:var(--text);margin-top:2px">${{item.tipo}} — ${{item.label}}</div>
          <div style="font-size:11px;color:var(--muted)">${{item.personas}} personas</div>
        </div>
      </div>`;
    }}).join('') + `
      <div style="margin-top:16px;background:#EEF2FF;border:1px solid #C7D2FE;border-radius:12px;padding:12px 14px">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <span style="font-size:11px;font-weight:700;color:#4F46E5;text-transform:uppercase;letter-spacing:.5px">Insight clave</span>
        </div>
        <div style="font-size:13px;color:#1E1B4B;line-height:1.5">
          ${{maxTipo.tipo}} concentra el ${{Math.round(maxTipo.personas/total*100)}}% de los participantes — ${{ratio}}x más que ${{minTipo.tipo}}
        </div>
      </div>`;
  }}
}}

function renderChartEvolucion() {{
  const ev = DATA.evolucion;
  const avg = DATA.kpis.pct_asistencia_global;
  chartEvolInst = new ApexCharts(document.getElementById('chartEvolucion'), {{
    ...baseChartOpts(),
    chart: {{ ...baseChartOpts().chart, type:'area', height:280, zoom:{{ enabled:false }} }},
    series: [{{ name:'% Asistencia', data:ev.map(e=>e.pct) }}],
    xaxis: {{ categories:ev.map(e=>fmtDate(e.fecha)), labels:{{ rotate:-45, style:{{ fontSize:'11px' }} }}, axisBorder:{{ show:false }} }},
    yaxis: {{ min:0, max:100, labels:{{ formatter:v=>v+'%' }} }},
    grid: {{ show:false }},
    annotations: {{
      yaxis: [{{
        y: avg,
        borderColor: '#94A3B8',
        borderWidth: 1,
        strokeDashArray: 4
      }}]
    }},
    markers: {{
      size: 5,
      colors: ['#4F46E5'],
      strokeColors: ['#3730A3'],
      strokeWidth: 2,
      hover: {{ size: 7 }},
      discrete: ev.map((e, i) => e.evento ? {{
        seriesIndex: 0, dataPointIndex: i,
        fillColor: '#F59E0B', strokeColor: '#D97706', size: 7
      }} : null).filter(Boolean)
    }},
    dataLabels: {{
      enabled: true,
      formatter: v => v + '%',
      style: {{ fontSize:'11px', fontWeight:700, colors:['#4F46E5'] }},
      background: {{ enabled:false }},
      offsetY: -6
    }},
    fill: {{ type:'gradient', gradient:{{ type:'vertical', shadeIntensity:0, inverseColors:false, opacityFrom:0.4, opacityTo:0.02, stops:[0,95,100] }} }},
    stroke: {{ curve:'smooth', width:2.5 }},
    colors: ['#4F46E5'],
    legend: {{ show:false }},
    tooltip: {{
      custom: function({{ dataPointIndex }}) {{
        const e = ev[dataPointIndex];
        const evLabel = e.evento ? `<div style="font-size:11px;color:#92400E;font-weight:600;margin-top:2px">★ ${{e.evento}}</div>` : '';
        return `<div style="padding:10px 14px;font-family:Inter,sans-serif;min-width:160px">
          <div style="font-size:12px;font-weight:600;color:var(--text)">${{fmtDate(e.fecha)}}</div>
          ${{evLabel}}
          <div style="font-size:20px;font-weight:800;color:#4F46E5;margin-top:4px">${{e.pct}}%</div>
          <div style="font-size:11px;color:var(--muted)">${{e.asistentes}} / ${{e.total_aplica}} personas</div>
        </div>`;
      }}
    }},
  }});
  chartEvolInst.render();
  // Label del promedio en HTML estático (no annotation label de ApexCharts)
  const evolPromLabel = document.getElementById('evolPromLabel');
  if (evolPromLabel) evolPromLabel.querySelector('span').textContent = `Promedio ${{avg}}%`;
  // Tarjetas de resumen
  const best = ev.reduce((a,b) => a.pct > b.pct ? a : b);
  const worst = ev.reduce((a,b) => a.pct < b.pct ? a : b);
  const primera = fmtDate(ev[0].fecha);
  const ultima = fmtDate(ev[ev.length-1].fecha);
  const avgPersonas = Math.round(ev.reduce((s,e)=>s+e.asistentes,0)/ev.length);
  const cards = [
    {{ label:'Mejor semana', val:best.pct+'%', sub:fmtDate(best.fecha)+(best.evento?' · '+best.evento:''), col:'#10B981',
       icon:`<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>` }},
    {{ label:'Peor semana',  val:worst.pct+'%', sub:fmtDate(worst.fecha)+(worst.evento?' · '+worst.evento:''), col:'#EF4444',
       icon:`<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>` }},
    {{ label:'Promedio semanal', val:avgPersonas, sub:'personas por sesión', col:'#4F46E5',
       icon:`<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>` }},
    {{ label:'Semanas', val:ev.length, sub:`${{primera}} – ${{ultima}}`, col:'#0EA5E9',
       icon:`<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>` }},
  ];
  const evolEl = document.getElementById('evolStats');
  if (evolEl) {{
    evolEl.innerHTML = `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px">
      ${{cards.map(c=>`
        <div style="background:var(--surface2);border-radius:12px;padding:16px;text-align:center">
          <div style="display:flex;justify-content:center;margin-bottom:10px">
            <div style="width:32px;height:32px;border-radius:8px;background:${{c.col}}18;display:flex;align-items:center;justify-content:center">
              ${{c.icon}}
            </div>
          </div>
          <div style="font-size:22px;font-weight:800;color:${{c.col}};line-height:1">${{c.val}}</div>
          <div style="font-size:11px;font-weight:600;color:var(--text);margin-top:4px">${{c.label}}</div>
          <div style="font-size:10px;color:var(--muted);margin-top:2px">${{c.sub}}</div>
        </div>`).join('')}}
    </div>`;
  }}
}}

function renderChartQ1Q2() {{
  const g = DATA.grupos;
  const el = document.getElementById('chartQ1Q2');
  el.style.height = '340px';
  chartQ1Q2Inst = new ApexCharts(el, {{
    ...baseChartOpts(),
    chart: {{ ...baseChartOpts().chart, type:'bar', height:340 }},
    series: [
      {{ name:'Q1 (Ene–Mar)', data:g.map(x=>x.pct_q1) }},
      {{ name:'Q2 (Abr+)',    data:g.map(x=>x.pct_q2) }},
    ],
    xaxis: {{
      categories: g.map(x=>x.nombre),
      labels: {{ rotate:-40, rotateAlways:true, style:{{ fontSize:'10px', fontWeight:500 }} }},
      axisBorder: {{ show:false }},
      axisTicks: {{ show:false }}
    }},
    yaxis: {{ min:0, max:100, labels:{{ formatter:v=>v+'%', style:{{ fontSize:'11px' }} }} }},
    plotOptions: {{ bar:{{ horizontal:false, borderRadius:4, columnWidth:'60%', dataLabels:{{ position:'top' }} }} }},
    grid: {{ show:false }},
    dataLabels: {{ enabled: false }},
    colors: ['#4F46E5','#10B981'],
    legend: {{ position:'top', fontSize:'12px', markers:{{ radius:4 }} }},
    stroke: {{ show:true, width:2, colors:['transparent'] }},
    tooltip: {{
      custom: function({{ dataPointIndex }}) {{
        const grp = g[dataPointIndex];
        return `<div style="padding:10px 14px;font-family:Inter,sans-serif">
          <div style="font-size:12px;font-weight:700;margin-bottom:8px">${{grp.nombre}}</div>
          <div style="display:flex;flex-direction:column;gap:4px">
            <div style="font-size:12px"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#4F46E5;margin-right:6px"></span>Q1: <b>${{grp.pct_q1}}%</b></div>
            <div style="font-size:12px"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#10B981;margin-right:6px"></span>Q2: <b>${{grp.pct_q2}}%</b></div>
          </div>
        </div>`;
      }}
    }},
  }});
  chartQ1Q2Inst.render();
}}

// ── TABLE: GRUPOS ─────────────────────────────────────────────────────────
function renderTableGrupos() {{
  const tipo=document.getElementById('filterGrupoTipo').value;
  const q=document.getElementById('filterGrupoQ').value;
  let grupos=DATA.grupos.filter(g=>!tipo||g.tipo_grupo===tipo);
  grupos=sortBy(grupos,sortState.grupos.key,sortState.grupos.dir);
  applySortIndicators('g',sortState.grupos);
  const sd=g=>g.status_dist||{{}};
  document.getElementById('tbodyGrupos').innerHTML=grupos.map(g=>{{
    const pct=q==='q1'?g.pct_q1:q==='q2'?g.pct_q2:g.pct_asistencia;
    return`<tr class="clickable" data-nombre="${{g.nombre}}" onclick="openGroupDrilldown(this.dataset.nombre)">
      <td data-label="Grupo"><strong>${{g.nombre}}</strong></td>
      <td data-label="Tipo">${{g.tipo_grupo||'-'}}</td>
      <td data-label="Personas">${{g.num_miembros}}</td>
      <td data-label="Sesiones">${{g.sesiones_totales}}</td>
      <td data-label="% Asist.">${{pctBar(pct)}}</td>
      <td data-label="Formales">${{g.num_miembros_formales}}</td>
      <td data-label="% Memb."><span style="font-weight:600;color:#4F46E5">${{g.pct_membresia}}%</span></td>
      <td data-label="Fieles"><span style="color:#10B981;font-weight:700">${{sd(g).Fiel||0}}</span></td>
      <td data-label="Activos"><span style="color:#4F46E5;font-weight:700">${{sd(g).Activo||0}}</span></td>
      <td data-label="Inconst."><span style="color:#F59E0B;font-weight:700">${{sd(g).Inconstante||0}}</span></td>
      <td data-label="Inactivos"><span style="color:#EF4444;font-weight:700">${{sd(g).Inactivo||0}}</span></td>
    </tr>`;
  }}).join('');
}}

// ── MATRIX ────────────────────────────────────────────────────────────────
function updateMatrixGrupos() {{
  const tipo=document.getElementById('filterMatrixTipo').value;
  const sel=document.getElementById('filterMatrixGrupo');
  const prev=sel.value;
  sel.innerHTML='<option value="">Todos los grupos</option>';
  [...new Set(DATA.personas.filter(p=>!tipo||p.tipo_grupo===tipo).map(p=>p.grupo_actual))].sort()
    .forEach(g=>{{const o=document.createElement('option');o.value=g;o.text=g;if(g===prev)o.selected=true;sel.appendChild(o);}});
}}
function renderMatrix() {{
  const tipo=document.getElementById('filterMatrixTipo').value;
  const grupo=document.getElementById('filterMatrixGrupo').value;
  const personas=DATA.personas.filter(p=>(!tipo||p.tipo_grupo===tipo)&&(!grupo||p.grupo_actual===grupo));
  const order=['Fiel','Activo','Inconstante','Inactivo'];
  const M={{}};
  order.forEach(s1=>{{M[s1]={{}};order.forEach(s2=>M[s1][s2]=0);}});
  personas.forEach(p=>{{if(p.status_q1&&p.status_q2&&M[p.status_q1])M[p.status_q1][p.status_q2]=(M[p.status_q1][p.status_q2]||0)+1;}});
  let html=`<tr><th>Q1 \\ Q2</th>${{order.map(s=>`<th>${{s}}</th>`).join('')}}</tr>`;
  order.forEach(s1=>{{
    const rowTotal=order.reduce((sum,s2)=>sum+(M[s1][s2]||0),0);
    if(rowTotal===0)return;
    html+=`<tr><th>${{s1}}</th>`;
    order.forEach(s2=>{{
      const v=M[s1][s2]||0;
      const si=order.indexOf(s1),sj=order.indexOf(s2);
      const cls=v===0?'m-zero':si===sj?'m-same':sj<si?'m-up':'m-down';
      html+=`<td class="${{cls}}">${{v||'-'}}</td>`;
    }});
    html+='</tr>';
  }});
  document.getElementById('matrixTable').innerHTML=html;
}}

// ── TABLE: RIESGO ─────────────────────────────────────────────────────────
function renderRiesgo() {{
  const tipo=document.getElementById('filterRiesgoTipo').value;
  let lista=(DATA.at_risk||[]).filter(p=>!tipo||p.tipo_grupo===tipo);
  lista=sortBy(lista,sortState.riesgo.key,sortState.riesgo.dir);
  applySortIndicators('r',sortState.riesgo);
  document.getElementById('tbodyRiesgo').innerHTML=lista.map(p=>
    `<tr class="clickable" data-nombre="${{p.nombre_completo}}" onclick="openDrilldown(this.dataset.nombre)">
      <td data-label="Nombre"><strong>${{p.nombre_completo}}</strong></td>
      <td data-label="Grupo">${{p.grupo_actual}}</td>
      <td data-label="Tipo">${{p.tipo_grupo||'-'}}</td>
      <td data-label="% Total">${{pctBar(p.pct_total)}}</td>
      <td data-label="Status">${{badgeHtml(p.status)}}</td>
      <td data-label="Ausente">${{weeksAgo(p.ultima_asistencia)}}</td>
    </tr>`
  ).join('');
}}

// ── TABLE: PERSONAS ───────────────────────────────────────────────────────
function renderPersonas() {{
  const search=document.getElementById('searchPersona').value.toLowerCase();
  const grupo=document.getElementById('filterPGrupo').value;
  const tipo=document.getElementById('filterPTipo').value;
  const status=document.getElementById('filterPStatus').value;
  let list=DATA.personas.filter(p=>
    (!search||p.nombre_completo.toLowerCase().includes(search))&&
    (!grupo||p.grupo_actual===grupo)&&
    (!tipo||p.tipo_grupo===tipo)&&
    (!status||p.status===status)
  );
  list=sortBy(list,sortState.personas.key,sortState.personas.dir);
  applySortIndicators('p',sortState.personas);
  document.getElementById('tbodyPersonas').innerHTML=list.map(p=>
    `<tr class="clickable" data-nombre="${{p.nombre_completo}}" onclick="openDrilldown(this.dataset.nombre)">
      <td data-label="Nombre"><strong>${{p.nombre_completo}}</strong></td>
      <td data-label="Grupo">${{p.grupo_actual}}</td>
      <td data-label="Tipo">${{p.tipo_grupo||'-'}}</td>
      <td data-label="Rol">${{p.rol||'-'}}</td>
      <td data-label="Q1%" style="font-weight:600;color:${{pctColor(p.pct_q1)}}">${{p.pct_q1}}%</td>
      <td data-label="Q2%" style="font-weight:600;color:${{pctColor(p.pct_q2)}}">${{p.pct_q2}}%</td>
      <td data-label="Total%">${{pctBar(p.pct_total)}}</td>
      <td data-label="Status">${{badgeHtml(p.status)}}</td>
    </tr>`
  ).join('');
}}

// ── EXPORT CSV ────────────────────────────────────────────────────────────
function exportCSV(tabla) {{
  let headers,rows;
  if(tabla==='personas') {{
    headers=['Nombre','Grupo','Tipo','Rol','Q1%','Q2%','Total%','Status'];
    const s=document.getElementById('filterPStatus').value;
    const g=document.getElementById('filterPGrupo').value;
    const t=document.getElementById('filterPTipo').value;
    rows=DATA.personas.filter(p=>(!s||p.status===s)&&(!g||p.grupo_actual===g)&&(!t||p.tipo_grupo===t))
      .map(p=>[p.nombre_completo,p.grupo_actual,p.tipo_grupo||'',p.rol||'',p.pct_q1,p.pct_q2,p.pct_total,p.status]);
  }} else if(tabla==='grupos') {{
    headers=['Grupo','Tipo','Personas','Sesiones','%Asist','%Memb','Fieles','Activos','Inconstantes','Inactivos'];
    const tipo=document.getElementById('filterGrupoTipo').value;
    rows=DATA.grupos.filter(g=>!tipo||g.tipo_grupo===tipo).map(g=>{{
      const sd=g.status_dist||{{}};
      return[g.nombre,g.tipo_grupo||'',g.num_miembros,g.sesiones_totales,g.pct_asistencia,g.pct_membresia,sd.Fiel||0,sd.Activo||0,sd.Inconstante||0,sd.Inactivo||0];
    }});
  }} else {{
    headers=['Nombre','Grupo','Tipo','%Total','Status','Ultima Asistencia'];
    const tipo=document.getElementById('filterRiesgoTipo').value;
    rows=(DATA.at_risk||[]).filter(p=>!tipo||p.tipo_grupo===tipo)
      .map(p=>[p.nombre_completo,p.grupo_actual,p.tipo_grupo||'',p.pct_total,p.status,p.ultima_asistencia||'Nunca']);
  }}
  const csv=[headers,...rows].map(r=>r.map(v=>`"${{String(v).replace(/"/g,'""')}}"`).join(',')).join('\\n');
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,\\uFEFF'+encodeURIComponent(csv);
  a.download=`j1-${{tabla}}-${{new Date().toISOString().slice(0,10)}}.csv`;
  a.click();
}}

// ── PERSON DRILLDOWN ──────────────────────────────────────────────────────
let drillChart=null;
function openDrilldown(name) {{
  const p=DATA.personas.find(x=>x.nombre_completo===name);
  if(!p)return;
  let rachaHtml='';
  if(p.racha_actual&&p.racha_actual!==0) {{
    const r=p.racha_actual,abs=Math.abs(r);
    const cls=r>0?'racha-pos':'racha-neg',icon=r>0?'🔥':'❄️';
    const txt=r>0?`${{abs}} semana${{abs>1?'s':''}} asistiendo consecutivamente`:`${{abs}} semana${{abs>1?'s':''}} sin asistir`;
    rachaHtml=`<div class="racha-badge ${{cls}}">${{icon}} ${{txt}}</div>`;
  }}
  document.getElementById('modalContent').innerHTML=`
    <div style="font-size:22px;font-weight:800;padding-right:40px;margin-bottom:4px">${{p.nombre_completo}}</div>
    <div style="font-size:13px;color:var(--muted);margin-bottom:16px;display:flex;flex-wrap:wrap;gap:8px">
      <span>📌 ${{p.grupo_actual}}</span>
      <span>🏷️ ${{p.tipo_grupo||'-'}}</span>
      <span>👤 ${{p.rol||'Sin rol'}}</span>
      <span>🎓 ${{p.tipo_miembro||'No miembro'}}</span>
      ${{p.at_risk?'<span class="badge badge-riesgo">En riesgo</span>':''}}
    </div>
    ${{rachaHtml}}
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
      <div class="modal-stat"><div class="modal-stat-val" style="color:${{pctColor(p.pct_q1)}}">${{p.pct_q1}}%</div><div class="modal-stat-lbl">Q1 (${{p.asist_q1}}/${{p.total_q1}})</div>${{p.status_q1?`<div style="margin-top:4px">${{badgeHtml(p.status_q1)}}</div>`:''}}</div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:${{pctColor(p.pct_q2)}}">${{p.pct_q2}}%</div><div class="modal-stat-lbl">Q2 (${{p.asist_q2}}/${{p.total_q2}})</div>${{p.status_q2?`<div style="margin-top:4px">${{badgeHtml(p.status_q2)}}</div>`:''}}</div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:${{pctColor(p.pct_total)}}">${{p.pct_total}}%</div><div class="modal-stat-lbl">Total (${{p.total_asistencias}}/${{p.total_sesiones}})</div><div style="margin-top:4px">${{badgeHtml(p.status)}}</div></div>
    </div>
    <div style="font-size:14px;font-weight:600;margin-bottom:10px">Historial <span style="font-size:12px;font-weight:400;color:var(--muted)">✓ asistió · ✗ faltó · ★ evento</span></div>
    <div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:20px" id="modalTL"></div>
    <div id="modalChart" style="height:120px"></div>
  `;
  const fechasAsistidas=new Set(p.sesiones.filter(s=>s.asistio).map(s=>s.fecha));
  document.getElementById('modalTL').innerHTML=p.sesiones.map(s=>{{
    const cls=s.evento?'evento':s.asistio?'asistio':'falto';
    const icon=s.asistio?'✓':'✗';
    const lbl=s.evento?fmtDate(s.fecha)+' '+s.evento:fmtDate(s.fecha);
    const qStyle=s.quarter==='Q2'?'outline:2px solid #10B98140;outline-offset:-2px':'';
    return`<div class="tl-dot ${{cls}}" style="${{qStyle}}">${{icon}}<span class="tl-label">${{fmtDate(s.fecha)}}</span><span class="tt">${{lbl}}</span></div>`;
  }}).join('');
  if(drillChart){{drillChart.destroy();drillChart=null;}}
  drillChart=new ApexCharts(document.getElementById('modalChart'),{{
    ...baseChartOpts(),
    chart:{{...baseChartOpts().chart,type:'bar',height:120,sparkline:{{enabled:false}}}},
    series:[{{name:'%',data:[p.pct_q1,p.pct_q2,p.pct_total]}}],
    xaxis:{{categories:['Q1','Q2','Total']}},
    yaxis:{{min:0,max:100,labels:{{formatter:v=>v+'%'}}}},
    plotOptions:{{bar:{{borderRadius:4,distributed:true}}}},
    colors:[pctColor(p.pct_q1),pctColor(p.pct_q2),pctColor(p.pct_total)],
    dataLabels:{{enabled:true,formatter:v=>v+'%',style:{{fontWeight:700}}}},
    legend:{{show:false}},
    tooltip:{{y:{{formatter:v=>v+'%'}}}},
  }});
  drillChart.render();
  document.getElementById('modalOverlay').classList.add('open');
}}

// ── GROUP DRILLDOWN ───────────────────────────────────────────────────────
function openGroupDrilldown(groupName) {{
  const members=DATA.personas.filter(p=>p.grupo_actual===groupName);
  if(!members.length)return;
  const g=DATA.grupos.find(x=>x.nombre===groupName)||{{}};
  const sd=g.status_dist||{{}};
  const dateSet=new Set(members.flatMap(m=>m.sesiones_grupo.map(s=>s.fecha)));
  const dates=[...dateSet].sort();
  const gEv=dates.map(fecha=>{{
    const tot=members.filter(m=>m.sesiones_grupo.some(s=>s.fecha===fecha)).length;
    const att=members.filter(m=>m.sesiones_grupo.some(s=>s.fecha===fecha&&s.asistio)).length;
    const evento=(DATA.eventos||{{}})[fecha]||null;
    return{{fecha,tot,att,pct:tot>0?Math.round(att/tot*100):0,evento}};
  }});
  const bottom5=[...members].sort((a,b)=>a.pct_total-b.pct_total).slice(0,5);
  document.getElementById('modalContent').innerHTML=`
    <div style="font-size:22px;font-weight:800;padding-right:40px;margin-bottom:4px">${{groupName}}</div>
    <div style="font-size:13px;color:var(--muted);margin-bottom:16px;display:flex;gap:12px">
      <span>🏷️ ${{g.tipo_grupo||'-'}}</span>
      <span>👥 ${{members.length}} personas</span>
      <span>📅 ${{dates.length}} sesiones</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px">
      <div class="modal-stat"><div class="modal-stat-val" style="color:#10B981">${{sd.Fiel||0}}</div><div class="modal-stat-lbl">Fieles</div></div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:#4F46E5">${{sd.Activo||0}}</div><div class="modal-stat-lbl">Activos</div></div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:#F59E0B">${{sd.Inconstante||0}}</div><div class="modal-stat-lbl">Inconstantes</div></div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:#EF4444">${{sd.Inactivo||0}}</div><div class="modal-stat-lbl">Inactivos</div></div>
    </div>
    <div style="font-size:14px;font-weight:600;margin-bottom:10px">Evolución del grupo</div>
    <div id="modalChart" style="height:180px;margin-bottom:20px"></div>
    <div style="font-size:14px;font-weight:600;margin-bottom:10px">Menor asistencia <span style="font-size:12px;font-weight:400;color:var(--muted)">(click para ver detalle)</span></div>
    <div style="overflow-x:auto"><table class="mini-table"><thead><tr><th>Nombre</th><th>% Total</th><th>Status</th></tr></thead><tbody id="groupMembersTbody"></tbody></table></div>
  `;
  document.getElementById('groupMembersTbody').innerHTML=bottom5.map(p=>
    `<tr class="clickable" data-nombre="${{p.nombre_completo}}" onclick="openDrilldown(this.dataset.nombre)">
      <td><strong>${{p.nombre_completo}}</strong></td>
      <td>${{pctBar(p.pct_total)}}</td>
      <td>${{badgeHtml(p.status)}}</td>
    </tr>`
  ).join('');
  if(drillChart){{drillChart.destroy();drillChart=null;}}
  drillChart=new ApexCharts(document.getElementById('modalChart'),{{
    ...baseChartOpts(),
    chart:{{...baseChartOpts().chart,type:'area',height:180}},
    series:[{{name:'% Asist.',data:gEv.map(e=>e.pct)}}],
    xaxis:{{categories:gEv.map(e=>fmtDate(e.fecha)+(e.evento?' ★':'')),labels:{{rotate:-40,style:{{fontSize:'10px'}}}}}},
    yaxis:{{min:0,max:100,labels:{{formatter:v=>v+'%'}}}},
    grid:{{show:false}},
    fill:{{type:'gradient',gradient:{{opacityFrom:0.12,opacityTo:0}}}},
    stroke:{{curve:'smooth',width:2.5}},
    colors:['#4F46E5'],
    legend:{{show:false}},
    markers:{{size:gEv.map(e=>e.evento?6:3),colors:gEv.map(e=>e.evento?'#F59E0B':'#4F46E5')}},
    tooltip:{{custom:function({{dataPointIndex}}){{
      const e=gEv[dataPointIndex];
      return`<div style="padding:8px 12px;font-family:Inter,sans-serif">
        <div style="font-weight:600">${{fmtDate(e.fecha)}}${{e.evento?' — '+e.evento:''}}</div>
        <div style="font-size:18px;font-weight:800;color:#4F46E5">${{e.pct}}%</div>
        <div style="font-size:11px;color:var(--muted)">${{e.att}}/${{e.tot}} personas</div>
      </div>`;
    }}}},
  }});
  drillChart.render();
  document.getElementById('modalOverlay').classList.add('open');
}}

// ── MODAL CLOSE ───────────────────────────────────────────────────────────
function closeModal(e) {{ if(e.target===document.getElementById('modalOverlay'))closeModalDirect(); }}
function closeModalDirect() {{
  document.getElementById('modalOverlay').classList.remove('open');
  if(drillChart){{drillChart.destroy();drillChart=null;}}
}}

// ── INIT ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{{
  const d=DATA.generated_at?new Date(DATA.generated_at):new Date();
  document.getElementById('lastUpdated').textContent=
    'Actualizado: '+d.toLocaleString('es-PE',{{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}});

  renderKPIs();
  renderRankingGrupos();
  renderChartTipos();
  renderChartEvolucion();
  renderChartQ1Q2();
  renderTableGrupos();
  renderMatrix();
  renderRiesgo();

  const gSel=document.getElementById('filterPGrupo');
  [...new Set(DATA.personas.map(p=>p.grupo_actual))].sort().forEach(g=>{{
    const o=document.createElement('option');o.value=g;o.text=g;gSel.appendChild(o);
  }});
  updateMatrixGrupos();
  renderPersonas();
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
