"""
Tool: generate_dashboard.py
Genera dashboard.html a partir de .tmp/asistencia_processed.json y lo abre en el browser.
"""

import json
import os
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"
OUTPUT_PATH = ROOT / ".tmp" / "dashboard.html"


def main():
    processed_path = TMP_DIR / "asistencia_processed.json"
    if not processed_path.exists():
        print("[ERROR] .tmp/asistencia_processed.json no encontrado. Ejecuta primero process_data.py")
        sys.exit(1)

    with open(processed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data_json = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Asistencia J1 - Alianza de Monterrico</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
:root {{
  --primary:#4F46E5; --primary-light:#EEF2FF;
  --success:#10B981; --warning:#F59E0B; --danger:#EF4444; --neutral:#6B7280;
  --bg:#F9FAFB; --card:#FFFFFF; --text:#111827; --text-muted:#6B7280;
  --border:#E5E7EB; --radius:12px;
  --shadow:0 1px 3px rgba(0,0,0,.1),0 1px 2px rgba(0,0,0,.06);
  --shadow-lg:0 10px 15px rgba(0,0,0,.1),0 4px 6px rgba(0,0,0,.05);
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text)}}
.header{{background:var(--card);border-bottom:1px solid var(--border);padding:16px 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:var(--shadow)}}
.header h1{{font-size:20px;font-weight:700;color:var(--primary)}}
.header p{{font-size:13px;color:var(--text-muted);margin-top:2px}}
.last-updated{{font-size:12px;color:var(--text-muted);text-align:right;flex-shrink:0}}
.container{{max-width:1400px;margin:0 auto;padding:24px 32px}}
.tabs{{display:flex;gap:4px;background:var(--border);padding:4px;border-radius:8px;margin-bottom:24px;width:fit-content}}
.tab{{padding:8px 20px;border-radius:6px;border:none;background:transparent;cursor:pointer;font-size:14px;font-weight:500;color:var(--text-muted);transition:all .15s;white-space:nowrap}}
.tab.active{{background:var(--card);color:var(--primary);box-shadow:var(--shadow)}}
.tab-icon{{margin-right:4px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}}
.kpi-card{{background:var(--card);border-radius:var(--radius);padding:20px;border:1px solid var(--border);box-shadow:var(--shadow);transition:transform .15s}}
.kpi-card:hover{{transform:translateY(-2px);box-shadow:var(--shadow-lg)}}
.kpi-card.clickable{{cursor:pointer}}
.kpi-label{{font-size:12px;font-weight:500;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px}}
.kpi-value{{font-size:32px;font-weight:800;margin-top:6px}}
.kpi-value.fiel{{color:var(--success)}} .kpi-value.activo{{color:var(--primary)}}
.kpi-value.inconstante{{color:var(--warning)}} .kpi-value.inactivo{{color:var(--danger)}}
.kpi-value.riesgo{{color:#DC2626}}
.kpi-sub{{font-size:12px;color:var(--text-muted);margin-top:4px}}
.kpi-delta{{font-size:12px;font-weight:700;margin-top:4px}}
.kpi-delta.up{{color:var(--success)}} .kpi-delta.down{{color:var(--danger)}} .kpi-delta.flat{{color:var(--text-muted)}}
.charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
.chart-card{{background:var(--card);border-radius:var(--radius);padding:20px;border:1px solid var(--border);box-shadow:var(--shadow)}}
.chart-card.full{{grid-column:1/-1}}
.chart-title{{font-size:15px;font-weight:600;margin-bottom:16px}}
.table-section{{background:var(--card);border-radius:var(--radius);border:1px solid var(--border);box-shadow:var(--shadow);overflow:hidden;margin-bottom:24px}}
.table-header{{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
.table-title{{font-size:15px;font-weight:600}}
.filters{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.filter-select{{padding:6px 12px;border:1px solid var(--border);border-radius:6px;font-size:13px;background:var(--bg);color:var(--text);cursor:pointer}}
.search-input{{padding:6px 12px;border:1px solid var(--border);border-radius:6px;font-size:13px;background:var(--bg);color:var(--text);width:200px}}
.export-btn{{padding:6px 12px;border:1px solid var(--border);border-radius:6px;font-size:12px;font-weight:500;background:var(--bg);color:var(--text);cursor:pointer}}
.export-btn:hover{{background:var(--border)}}
.table-overflow{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse}}
th{{padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border);background:var(--bg);white-space:nowrap}}
th.sortable{{cursor:pointer;user-select:none}}
th.sortable:hover{{color:var(--primary)}}
th.sort-active{{color:var(--primary)}}
.sort-ind{{font-size:10px;margin-left:3px;opacity:.5}}
th.sort-active .sort-ind{{opacity:1}}
td{{padding:11px 16px;font-size:14px;border-bottom:1px solid var(--border)}}
tr:last-child td{{border-bottom:none}}
tr.clickable{{cursor:pointer;transition:background .1s}}
tr.clickable:hover{{background:var(--primary-light)}}
.badge{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:100px;font-size:12px;font-weight:600}}
.badge-fiel{{background:#D1FAE5;color:#065F46}} .badge-activo{{background:#EEF2FF;color:#3730A3}}
.badge-inconstante{{background:#FEF3C7;color:#92400E}} .badge-inactivo{{background:#FEE2E2;color:#991B1B}}
.badge-riesgo{{background:#FEE2E2;color:#991B1B}}
.pct-wrap{{display:flex;align-items:center;gap:8px}}
.pct-bar{{height:6px;border-radius:3px;flex:1;background:var(--border);overflow:hidden;min-width:60px}}
.pct-bar-fill{{height:100%;border-radius:3px}}
.pct-text{{font-size:13px;font-weight:600;min-width:40px;text-align:right}}
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:1000;align-items:center;justify-content:center}}
.modal-overlay.open{{display:flex}}
.modal{{background:var(--card);border-radius:16px;width:720px;max-width:95vw;max-height:90vh;overflow-y:auto;box-shadow:var(--shadow-lg);padding:28px;position:relative}}
.modal-close{{position:absolute;top:16px;right:16px;width:32px;height:32px;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;color:var(--text-muted);z-index:10}}
.modal-close:hover{{background:var(--border)}}
.modal-name{{font-size:22px;font-weight:800;margin-bottom:4px;padding-right:40px}}
.modal-meta{{font-size:13px;color:var(--text-muted);margin-bottom:16px;display:flex;flex-wrap:wrap;gap:8px}}
.modal-stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}}
.modal-stats-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}
.modal-stat{{background:var(--bg);border-radius:8px;padding:12px;text-align:center}}
.modal-stat-val{{font-size:22px;font-weight:800}}
.modal-stat-lbl{{font-size:11px;color:var(--text-muted);margin-top:2px}}
.racha-badge{{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:8px;font-size:13px;font-weight:600;margin-bottom:16px}}
.racha-pos{{background:#D1FAE5;color:#065F46}}
.racha-neg{{background:#FEE2E2;color:#991B1B}}
.timeline-title{{font-size:14px;font-weight:600;margin-bottom:10px;margin-top:4px}}
.timeline{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px}}
.tl-dot{{width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;position:relative;cursor:default;flex-direction:column}}
.tl-dot.asistio{{background:#D1FAE5;color:#065F46}}
.tl-dot.falto{{background:#FEE2E2;color:#991B1B}}
.tl-dot.evento{{background:#FEF3C7;border:2px solid #F59E0B;color:#92400E}}
.tl-dot .tt{{display:none;position:absolute;bottom:44px;left:50%;transform:translateX(-50%);background:var(--text);color:white;font-size:11px;padding:4px 8px;border-radius:4px;white-space:nowrap;z-index:10;pointer-events:none}}
.tl-dot:hover .tt{{display:block}}
.tl-label{{font-size:9px;margin-top:1px;opacity:.7}}
.section-title{{font-size:15px;font-weight:600;margin:20px 0 12px}}
.matrix-table{{width:auto;border-collapse:collapse;font-size:13px}}
.matrix-table th,.matrix-table td{{padding:8px 14px;border:1px solid var(--border);text-align:center}}
.matrix-table th{{background:var(--bg);font-weight:600}}
.m-same{{background:#F3F4F6;color:var(--text-muted)}}
.m-up{{background:#D1FAE5;color:#065F46;font-weight:700}}
.m-down{{background:#FEE2E2;color:#991B1B;font-weight:700}}
.m-zero{{color:var(--border)}}
.page{{display:none}} .page.active{{display:block}}
.alert-strip{{background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#991B1B;display:flex;align-items:center;gap:8px}}
.mini-table{{width:100%;border-collapse:collapse;font-size:13px}}
.mini-table th,.mini-table td{{padding:8px 12px;border-bottom:1px solid var(--border);text-align:left}}
.mini-table th{{background:var(--bg);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)}}
.mini-table tr:last-child td{{border-bottom:none}}
.mini-table tr.clickable:hover{{background:var(--primary-light)}}

/* ═══════════ RESPONSIVE MOBILE ═══════════ */
@media(max-width:768px){{
  .charts-grid{{grid-template-columns:1fr}}
  .container{{padding:16px}}
}}
@media(max-width:640px){{
  /* Header */
  .header{{flex-direction:column;align-items:flex-start;gap:4px;padding:10px 16px}}
  .last-updated{{font-size:11px;text-align:left}}
  /* Tabs: full width, icons only */
  .tabs{{width:100%;box-sizing:border-box}}
  .tab{{flex:1;padding:10px 4px;font-size:13px;text-align:center}}
  .tab-text{{display:none}}
  .tab-icon{{margin-right:0;font-size:18px}}
  /* KPIs: 2 columns */
  .kpi-grid{{grid-template-columns:repeat(2,1fr)!important}}
  .kpi-value{{font-size:26px}}
  /* Tables → Card layout */
  thead{{display:none}}
  tbody{{display:block;padding:8px}}
  tr.data-row{{display:block;border-radius:8px;border:1px solid var(--border);margin-bottom:10px;overflow:hidden;background:var(--card)}}
  tr.data-row td{{display:flex;justify-content:space-between;align-items:center;padding:9px 12px;border-bottom:1px solid var(--border);font-size:13px;min-height:42px}}
  tr.data-row td:last-child{{border-bottom:none}}
  tr.data-row td[data-label]::before{{content:attr(data-label);font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.4px;flex-shrink:0;min-width:72px;margin-right:8px}}
  /* Filters: horizontal scroll */
  .table-header{{flex-direction:column;align-items:flex-start;gap:8px}}
  .filters{{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:2px;width:100%}}
  .search-input{{width:140px}}
  /* Modal: bottom sheet */
  .modal-overlay{{align-items:flex-end}}
  .modal{{border-radius:16px 16px 0 0;max-height:88vh;padding:16px;width:100%;max-width:100vw}}
  .tl-dot{{width:30px;height:30px;font-size:12px}}
  .tl-label{{font-size:8px}}
  .modal-stats,.modal-stats-4{{gap:8px}}
  .modal-stat{{padding:8px}}
  .modal-stat-val{{font-size:18px}}
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>J1 - Alianza de Monterrico</h1>
    <p>Reporte de Asistencia Semanal</p>
  </div>
  <span class="last-updated" id="lastUpdated"></span>
</div>

<div class="container">
  <div class="tabs">
    <button class="tab active" data-page="overview" onclick="showPage('overview',this)"><span class="tab-icon">📊</span><span class="tab-text"> Resumen</span></button>
    <button class="tab" data-page="grupos" onclick="showPage('grupos',this)"><span class="tab-icon">👥</span><span class="tab-text"> Grupos</span></button>
    <button class="tab" data-page="riesgo" onclick="showPage('riesgo',this)"><span class="tab-icon">⚠️</span><span class="tab-text"> Riesgo</span></button>
    <button class="tab" data-page="personas" onclick="showPage('personas',this)"><span class="tab-icon">🙋</span><span class="tab-text"> Personas</span></button>
  </div>

  <!-- ===== RESUMEN ===== -->
  <div class="page active" id="page-overview">
    <div class="kpi-grid" id="kpiGrid" style="grid-template-columns:repeat(7,1fr)"></div>
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Asistencia por Grupo</div>
        <div id="chartGruposWrap" style="height:300px"><canvas id="chartGrupos"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Distribucion por Tipo (GBU / GDA / GDC)</div>
        <div style="height:300px"><canvas id="chartTipos"></canvas></div>
      </div>
      <div class="chart-card full">
        <div class="chart-title">Evolucion Semanal — % Asistencia <span style="font-size:12px;font-weight:400;color:var(--text-muted)">(puntos naranjas = eventos especiales)</span></div>
        <div style="height:240px"><canvas id="chartEvolucion"></canvas></div>
      </div>
    </div>
  </div>

  <!-- ===== GRUPOS ===== -->
  <div class="page" id="page-grupos">
    <div class="charts-grid">
      <div class="chart-card full">
        <div class="chart-title">Comparativa Q1 vs Q2 por Grupo</div>
        <div style="height:300px"><canvas id="chartQ1Q2"></canvas></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-title">Detalle por Grupo <span style="font-size:12px;font-weight:400;color:var(--text-muted)">(click fila para ver detalle)</span></span>
        <div class="filters">
          <select class="filter-select" id="filterGrupoTipo" onchange="renderTableGrupos()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option>
            <option value="GDA">GDA</option>
            <option value="GDC">GDC</option>
          </select>
          <select class="filter-select" id="filterGrupoQ" onchange="renderTableGrupos()">
            <option value="total">Total</option>
            <option value="q1">Q1</option>
            <option value="q2">Q2</option>
          </select>
          <button class="export-btn" onclick="exportCSV('grupos')">⬇ CSV</button>
        </div>
      </div>
      <div class="table-overflow">
        <table>
          <thead><tr>
            <th class="sortable" id="th-g-nombre" onclick="sortGrupos('nombre')">Grupo <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-g-tipo" onclick="sortGrupos('tipo_grupo')">Tipo <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-g-miembros" onclick="sortGrupos('num_miembros')">Miembros <span class="sort-ind">↕</span></th>
            <th>Sesiones</th>
            <th class="sortable" id="th-g-pct" onclick="sortGrupos('pct_asistencia')">% Asistencia <span class="sort-ind">↕</span></th>
            <th>Formales</th>
            <th class="sortable" id="th-g-mem" onclick="sortGrupos('pct_membresia')">% Memb. <span class="sort-ind">↕</span></th>
            <th>Fieles</th><th>Activos</th><th>Inconstantes</th><th>Inactivos</th>
          </tr></thead>
          <tbody id="tbodyGrupos"></tbody>
        </table>
      </div>
    </div>

    <div class="table-section">
      <div class="table-header">
        <span class="table-title">Cambios de Status Q1 → Q2</span>
        <div class="filters">
          <select class="filter-select" id="filterMatrixTipo" onchange="updateMatrixGrupos();renderMatrix()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option>
            <option value="GDA">GDA</option>
            <option value="GDC">GDC</option>
          </select>
          <select class="filter-select" id="filterMatrixGrupo" onchange="renderMatrix()">
            <option value="">Todos los grupos</option>
          </select>
        </div>
      </div>
      <div style="padding:20px;overflow-x:auto">
        <table class="matrix-table" id="matrixTable"></table>
      </div>
    </div>
  </div>

  <!-- ===== EN RIESGO ===== -->
  <div class="page" id="page-riesgo">
    <div class="alert-strip">
      ⚠ Personas con <strong>0 asistencias en las ultimas 4 sesiones de su grupo</strong>.
      Requieren seguimiento.
    </div>
    <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr))">
      <div class="kpi-card">
        <div class="kpi-label">Total en riesgo</div>
        <div class="kpi-value riesgo" id="kpiRiesgo">-</div>
        <div class="kpi-sub">de <span id="kpiTotal">-</span> participantes activos</div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-title">Listado de personas en riesgo</span>
        <div class="filters">
          <select class="filter-select" id="filterRiesgoTipo" onchange="renderRiesgo()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option>
            <option value="GDA">GDA</option>
            <option value="GDC">GDC</option>
          </select>
          <button class="export-btn" onclick="exportCSV('riesgo')">⬇ CSV</button>
        </div>
      </div>
      <div class="table-overflow">
        <table>
          <thead><tr>
            <th class="sortable" id="th-r-nombre" onclick="sortRiesgo('nombre_completo')">Nombre <span class="sort-ind">↕</span></th>
            <th class="sortable" id="th-r-grupo" onclick="sortRiesgo('grupo_actual')">Grupo <span class="sort-ind">↕</span></th>
            <th>Tipo</th>
            <th class="sortable" id="th-r-pct" onclick="sortRiesgo('pct_total')">% Total <span class="sort-ind">↕</span></th>
            <th>Status</th>
            <th class="sortable" id="th-r-ultima" onclick="sortRiesgo('ultima_asistencia')">Ultima asistencia <span class="sort-ind">↕</span></th>
          </tr></thead>
          <tbody id="tbodyRiesgo"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ===== PERSONAS ===== -->
  <div class="page" id="page-personas">
    <div class="table-section">
      <div class="table-header">
        <span class="table-title">Participantes</span>
        <div class="filters">
          <input class="search-input" id="searchPersona" placeholder="Buscar nombre..." oninput="renderPersonas()">
          <select class="filter-select" id="filterPGrupo" onchange="renderPersonas()"><option value="">Todos los grupos</option></select>
          <select class="filter-select" id="filterPTipo" onchange="renderPersonas()">
            <option value="">Todos los tipos</option>
            <option value="GBU">GBU</option>
            <option value="GDA">GDA</option>
            <option value="GDC">GDC</option>
          </select>
          <select class="filter-select" id="filterPStatus" onchange="renderPersonas()">
            <option value="">Todos los status</option>
            <option>Fiel</option><option>Activo</option><option>Inconstante</option><option>Inactivo</option>
          </select>
          <button class="export-btn" onclick="exportCSV('personas')">⬇ CSV</button>
        </div>
      </div>
      <div class="table-overflow">
        <table>
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
</div>

<!-- Modal drilldown -->
<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
  <div class="modal">
    <button class="modal-close" onclick="closeModalDirect()">✕</button>
    <div id="modalContent"></div>
  </div>
</div>

<script>
const DATA = {data_json};

// ── SORT KEY → ID MAP ──────────────────────────────────────────────────────
const KEY_TO_ID = {{
  nombre_completo:'nombre', grupo_actual:'grupo', tipo_grupo:'tipo',
  pct_total:'total', pct_q1:'q1', pct_q2:'q2', status:'status',
  pct_asistencia:'pct', num_miembros:'miembros', pct_membresia:'mem',
  ultima_asistencia:'ultima', nombre:'nombre',
}};

// ── UTILS ──────────────────────────────────────────────────────────────────
function pctColor(p){{
  return p>=80?'#10B981':p>=50?'#4F46E5':p>0?'#F59E0B':'#EF4444';
}}
function badgeHtml(s){{
  const m={{'Fiel':'fiel','Activo':'activo','Inconstante':'inconstante','Inactivo':'inactivo'}};
  return `<span class="badge badge-${{m[s]||'inactivo'}}">${{s}}</span>`;
}}
function pctBar(p){{
  return `<div class="pct-wrap"><div class="pct-bar"><div class="pct-bar-fill" style="width:${{p}}%;background:${{pctColor(p)}}"></div></div><span class="pct-text" style="color:${{pctColor(p)}}">${{p}}%</span></div>`;
}}
function fmtDate(iso){{const[y,m,d]=iso.split('-');return d+'/'+m;}}
function weeksAgo(isoDate){{
  if(!isoDate)return'Nunca';
  const ref=DATA.generated_at?new Date(DATA.generated_at):new Date();
  const days=Math.floor((ref-new Date(isoDate))/86400000);
  if(days<7)return'Esta semana';
  const w=Math.floor(days/7);
  return w===1?'Hace 1 semana':`Hace ${{w}} semanas`;
}}

// ── NAVIGATION ─────────────────────────────────────────────────────────────
function showPage(name,btn){{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  const target=btn||document.querySelector(`.tab[data-page="${{name}}"]`);
  if(target)target.classList.add('active');
}}
function navToStatus(page,status){{
  showPage(page);
  if(page==='personas'&&status){{
    document.getElementById('filterPStatus').value=status;
    renderPersonas();
  }}
}}

// ── SORT ───────────────────────────────────────────────────────────────────
const sortState={{
  personas:{{key:'pct_total',dir:-1}},
  grupos:{{key:'pct_asistencia',dir:-1}},
  riesgo:{{key:'grupo_actual',dir:1}},
}};

function applySortIndicators(prefix,state){{
  document.querySelectorAll(`[id^="th-${{prefix}}-"]`).forEach(th=>{{
    th.classList.remove('sort-active');
    const si=th.querySelector('.sort-ind');if(si)si.textContent='↕';
  }});
  const idSuffix=KEY_TO_ID[state.key]||state.key;
  const th=document.getElementById(`th-${{prefix}}-${{idSuffix}}`);
  if(th){{
    th.classList.add('sort-active');
    const si=th.querySelector('.sort-ind');if(si)si.textContent=state.dir>0?'↑':'↓';
  }}
}}
function sortBy(arr,key,dir){{
  return[...arr].sort((a,b)=>{{
    let av=a[key],bv=b[key];
    if(av==null||av==='')return 1;if(bv==null||bv==='')return -1;
    if(typeof av==='number')return(av-bv)*dir;
    return String(av).localeCompare(String(bv),'es')*dir;
  }});
}}
function sortPersonas(key){{
  sortState.personas.dir=(sortState.personas.key===key)?sortState.personas.dir*-1:(typeof DATA.personas[0][key]==='number'?-1:1);
  sortState.personas.key=key;renderPersonas();
}}
function sortGrupos(key){{
  sortState.grupos.dir=(sortState.grupos.key===key)?sortState.grupos.dir*-1:(typeof DATA.grupos[0][key]==='number'?-1:1);
  sortState.grupos.key=key;renderTableGrupos();
}}
function sortRiesgo(key){{
  const sample=(DATA.at_risk||[])[0]||{{}};
  sortState.riesgo.dir=(sortState.riesgo.key===key)?sortState.riesgo.dir*-1:(typeof sample[key]==='number'?-1:1);
  sortState.riesgo.key=key;renderRiesgo();
}}

// ── KPIs ───────────────────────────────────────────────────────────────────
function renderKPIs(){{
  const k=DATA.kpis,sd=k.status_dist||{{}};
  const ev=DATA.evolucion||[];
  let deltaHtml='';
  if(ev.length>=2){{
    const d=parseFloat((ev[ev.length-1].pct-ev[ev.length-2].pct).toFixed(1));
    const cls=d>0?'up':d<0?'down':'flat';
    const arrow=d>0?'↑':d<0?'↓':'→';
    deltaHtml=`<div class="kpi-delta ${{cls}}">${{arrow}} ${{d>0?'+':''}}${{d}}pp vs sem. anterior</div>`;
  }}
  document.getElementById('kpiGrid').innerHTML=[
    {{l:'Participantes',v:k.total_personas,sub:'con grupo activo',page:null}},
    {{l:'% Asistencia',v:k.pct_asistencia_global+'%',sub:'promedio general',page:null,extra:deltaHtml}},
    {{l:'Fieles',v:sd.Fiel||0,c:'fiel',sub:'80%+',page:'personas',status:'Fiel'}},
    {{l:'Activos',v:sd.Activo||0,c:'activo',sub:'51–79%',page:'personas',status:'Activo'}},
    {{l:'Inconstantes',v:sd.Inconstante||0,c:'inconstante',sub:'1–50%',page:'personas',status:'Inconstante'}},
    {{l:'Inactivos',v:sd.Inactivo||0,c:'inactivo',sub:'0%',page:'personas',status:'Inactivo'}},
    {{l:'En Riesgo',v:k.total_at_risk||0,c:'riesgo',sub:'0 asist. en 4 sem.',page:'riesgo'}},
  ].map(c=>{{
    const nav=c.page?`onclick="navToStatus('${{c.page}}','${{c.status||''}}')" tabindex="0"`:'';
    return`<div class="kpi-card${{c.page?' clickable':''}}" ${{nav}}>
      <div class="kpi-label">${{c.l}}</div>
      <div class="kpi-value ${{c.c||''}}">${{c.v}}</div>
      <div class="kpi-sub">${{c.sub}}</div>
      ${{c.extra||''}}
    </div>`;
  }}).join('');
  document.getElementById('kpiRiesgo').textContent=k.total_at_risk||0;
  document.getElementById('kpiTotal').textContent=k.total_personas;
}}

// ── CHARTS (touch-friendly) ─────────────────────────────────────────────────
const TOUCH={{interaction:{{mode:'nearest',intersect:false}},events:['click','mousemove','touchstart','touchmove']}};

function renderChartGrupos(){{
  const g=DATA.grupos.slice(0,20);
  document.getElementById('chartGruposWrap').style.height=Math.max(280,g.length*20)+'px';
  new Chart(document.getElementById('chartGrupos'),{{
    type:'bar',
    data:{{labels:g.map(x=>x.nombre),datasets:[{{label:'% Asistencia',data:g.map(x=>x.pct_asistencia),
      backgroundColor:g.map(x=>pctColor(x.pct_asistencia)+'CC'),
      borderColor:g.map(x=>pctColor(x.pct_asistencia)),borderWidth:1,borderRadius:5}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,...TOUCH,
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>` ${{c.parsed.x}}%`}}}}}},
      scales:{{x:{{min:0,max:100,grid:{{color:'#F3F4F6'}},ticks:{{callback:v=>v+'%'}}}},y:{{grid:{{display:false}}}}}}
    }}
  }});
}}
function renderChartTipos(){{
  const t=DATA.tipos;
  new Chart(document.getElementById('chartTipos'),{{
    type:'doughnut',
    data:{{labels:t.map(x=>`${{x.tipo}} - ${{x.label}}`),datasets:[{{data:t.map(x=>x.personas),
      backgroundColor:['#4F46E5CC','#10B981CC','#F59E0BCC','#EF4444CC'],borderWidth:2,borderColor:'#fff'}}]}},
    options:{{responsive:true,maintainAspectRatio:false,...TOUCH,
      plugins:{{legend:{{position:'bottom'}},tooltip:{{callbacks:{{label:c=>` ${{c.label}}: ${{c.parsed}} personas`}}}}}}
    }}
  }});
}}
function renderChartEvolucion(){{
  const ev=DATA.evolucion;
  new Chart(document.getElementById('chartEvolucion'),{{
    type:'line',
    data:{{
      labels:ev.map(e=>fmtDate(e.fecha)+(e.evento?' *':'')),
      datasets:[{{label:'% Asistencia',data:ev.map(e=>e.pct),
        borderColor:'#4F46E5',backgroundColor:'#4F46E520',tension:.3,fill:true,pointRadius:6,
        pointBackgroundColor:ev.map(e=>e.evento?'#F59E0B':'#4F46E5'),
        pointBorderColor:ev.map(e=>e.evento?'#D97706':'#3730A3'),
        pointBorderWidth:ev.map(e=>e.evento?2:1)}}]
    }},
    options:{{responsive:true,maintainAspectRatio:false,...TOUCH,
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{
        title:c=>{{const e=ev[c[0].dataIndex];return fmtDate(e.fecha)+(e.evento?' - '+e.evento:'')}},
        label:c=>` ${{c.parsed.y}}% (asistentes: ${{ev[c.dataIndex].asistentes}})`
      }}}}}},
      scales:{{y:{{min:0,max:100,grid:{{color:'#F3F4F6'}},ticks:{{callback:v=>v+'%'}}}},x:{{grid:{{display:false}}}}}}
    }}
  }});
}}
function renderChartQ1Q2(){{
  const g=DATA.grupos;
  new Chart(document.getElementById('chartQ1Q2'),{{
    type:'bar',
    data:{{labels:g.map(x=>x.nombre),datasets:[
      {{label:'Q1 (Ene-Mar)',data:g.map(x=>x.pct_q1),backgroundColor:'#4F46E599',borderRadius:4}},
      {{label:'Q2 (Abr+)',data:g.map(x=>x.pct_q2),backgroundColor:'#10B98199',borderRadius:4}},
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,...TOUCH,
      plugins:{{tooltip:{{callbacks:{{label:c=>` ${{c.dataset.label}}: ${{c.parsed.y}}%`}}}}}},
      scales:{{y:{{min:0,max:100,ticks:{{callback:v=>v+'%'}},grid:{{color:'#F3F4F6'}}}},x:{{grid:{{display:false}}}}}}
    }}
  }});
}}

// ── TABLE GRUPOS ───────────────────────────────────────────────────────────
function renderTableGrupos(){{
  const tipo=document.getElementById('filterGrupoTipo').value;
  const q=document.getElementById('filterGrupoQ').value;
  let grupos=DATA.grupos.filter(g=>!tipo||g.tipo_grupo===tipo);
  grupos=sortBy(grupos,sortState.grupos.key,sortState.grupos.dir);
  applySortIndicators('g',sortState.grupos);
  const sd=g=>g.status_dist||{{}};
  document.getElementById('tbodyGrupos').innerHTML=grupos.map(g=>{{
    const pct=q==='q1'?g.pct_q1:q==='q2'?g.pct_q2:g.pct_asistencia;
    return`<tr class="clickable data-row" data-nombre="${{g.nombre}}" onclick="openGroupDrilldown(this.dataset.nombre)">
      <td data-label="Grupo"><strong>${{g.nombre}}</strong></td>
      <td data-label="Tipo">${{g.tipo_grupo||'-'}}</td>
      <td data-label="Miembros">${{g.num_miembros}}</td>
      <td data-label="Sesiones">${{g.sesiones_totales}}</td>
      <td data-label="% Asist.">${{pctBar(pct)}}</td>
      <td data-label="Formales">${{g.num_miembros_formales}}</td>
      <td data-label="% Memb."><span style="font-weight:600;color:var(--primary)">${{g.pct_membresia}}%</span></td>
      <td data-label="Fieles"><span style="color:#10B981;font-weight:700">${{sd(g).Fiel||0}}</span></td>
      <td data-label="Activos"><span style="color:#4F46E5;font-weight:700">${{sd(g).Activo||0}}</span></td>
      <td data-label="Inconst."><span style="color:#F59E0B;font-weight:700">${{sd(g).Inconstante||0}}</span></td>
      <td data-label="Inactivos"><span style="color:#EF4444;font-weight:700">${{sd(g).Inactivo||0}}</span></td>
    </tr>`;
  }}).join('');
}}

// ── MATRIX ─────────────────────────────────────────────────────────────────
function updateMatrixGrupos(){{
  const tipo=document.getElementById('filterMatrixTipo').value;
  const sel=document.getElementById('filterMatrixGrupo');
  const prev=sel.value;
  sel.innerHTML='<option value="">Todos los grupos</option>';
  [...new Set(DATA.personas.filter(p=>!tipo||p.tipo_grupo===tipo).map(p=>p.grupo_actual))].sort()
    .forEach(g=>{{const o=document.createElement('option');o.value=g;o.text=g;if(g===prev)o.selected=true;sel.appendChild(o);}});
}}
function renderMatrix(){{
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

// ── EN RIESGO ──────────────────────────────────────────────────────────────
function renderRiesgo(){{
  const tipo=document.getElementById('filterRiesgoTipo').value;
  let lista=(DATA.at_risk||[]).filter(p=>!tipo||p.tipo_grupo===tipo);
  lista=sortBy(lista,sortState.riesgo.key,sortState.riesgo.dir);
  applySortIndicators('r',sortState.riesgo);
  document.getElementById('tbodyRiesgo').innerHTML=lista.map(p=>{{
    return`<tr class="clickable data-row" data-nombre="${{p.nombre_completo}}" onclick="openDrilldown(this.dataset.nombre)">
      <td data-label="Nombre"><strong>${{p.nombre_completo}}</strong></td>
      <td data-label="Grupo">${{p.grupo_actual}}</td>
      <td data-label="Tipo">${{p.tipo_grupo||'-'}}</td>
      <td data-label="% Total">${{pctBar(p.pct_total)}}</td>
      <td data-label="Status">${{badgeHtml(p.status)}}</td>
      <td data-label="Ausente">${{weeksAgo(p.ultima_asistencia)}}</td>
    </tr>`;
  }}).join('');
}}

// ── TABLE PERSONAS ─────────────────────────────────────────────────────────
function renderPersonas(){{
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
  document.getElementById('tbodyPersonas').innerHTML=list.map(p=>{{
    return`<tr class="clickable data-row" data-nombre="${{p.nombre_completo}}" onclick="openDrilldown(this.dataset.nombre)">
      <td data-label="Nombre"><strong>${{p.nombre_completo}}</strong></td>
      <td data-label="Grupo">${{p.grupo_actual}}</td>
      <td data-label="Tipo">${{p.tipo_grupo||'-'}}</td>
      <td data-label="Rol">${{p.rol||'-'}}</td>
      <td data-label="Q1%" style="font-weight:600;color:${{pctColor(p.pct_q1)}}">${{p.pct_q1}}%</td>
      <td data-label="Q2%" style="font-weight:600;color:${{pctColor(p.pct_q2)}}">${{p.pct_q2}}%</td>
      <td data-label="Total%">${{pctBar(p.pct_total)}}</td>
      <td data-label="Status">${{badgeHtml(p.status)}}</td>
    </tr>`;
  }}).join('');
}}

// ── EXPORT CSV ─────────────────────────────────────────────────────────────
function exportCSV(tabla){{
  let headers,rows;
  if(tabla==='personas'){{
    headers=['Nombre','Grupo','Tipo','Rol','Q1%','Q2%','Total%','Status'];
    const s=document.getElementById('filterPStatus').value;
    const g=document.getElementById('filterPGrupo').value;
    const t=document.getElementById('filterPTipo').value;
    const list=DATA.personas.filter(p=>(!s||p.status===s)&&(!g||p.grupo_actual===g)&&(!t||p.tipo_grupo===t));
    rows=list.map(p=>[p.nombre_completo,p.grupo_actual,p.tipo_grupo||'',p.rol||'',p.pct_q1,p.pct_q2,p.pct_total,p.status]);
  }}else if(tabla==='grupos'){{
    headers=['Grupo','Tipo','Miembros','Sesiones','%Asist','%Memb','Fieles','Activos','Inconstantes','Inactivos'];
    const tipo=document.getElementById('filterGrupoTipo').value;
    const list=DATA.grupos.filter(g=>!tipo||g.tipo_grupo===tipo);
    rows=list.map(g=>{{const sd=g.status_dist||{{}};return[g.nombre,g.tipo_grupo||'',g.num_miembros,g.sesiones_totales,g.pct_asistencia,g.pct_membresia,sd.Fiel||0,sd.Activo||0,sd.Inconstante||0,sd.Inactivo||0];}});
  }}else{{
    headers=['Nombre','Grupo','Tipo','%Total','Status','Ultima Asistencia'];
    const tipo=document.getElementById('filterRiesgoTipo').value;
    const list=(DATA.at_risk||[]).filter(p=>!tipo||p.tipo_grupo===tipo);
    rows=list.map(p=>[p.nombre_completo,p.grupo_actual,p.tipo_grupo||'',p.pct_total,p.status,p.ultima_asistencia||'Nunca']);
  }}
  const csv=[headers,...rows].map(r=>r.map(v=>`"${{String(v).replace(/"/g,'""')}}"`).join(',')).join('\\n');
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,\\uFEFF'+encodeURIComponent(csv);
  a.download=`j1-${{tabla}}-${{new Date().toISOString().slice(0,10)}}.csv`;
  a.click();
}}

// ── PERSON DRILLDOWN ───────────────────────────────────────────────────────
let drillChart=null;
function openDrilldown(name){{
  const p=DATA.personas.find(x=>x.nombre_completo===name);
  if(!p)return;

  let rachaHtml='';
  if(p.racha_actual!==undefined&&p.racha_actual!==0){{
    const r=p.racha_actual;
    const cls=r>0?'racha-pos':'racha-neg';
    const icon=r>0?'🔥':'❄️';
    const abs=Math.abs(r);
    const txt=r>0?`${{abs}} semana${{abs>1?'s':''}} asistiendo consecutivamente`:`${{abs}} semana${{abs>1?'s':''}} sin asistir seguidas`;
    rachaHtml=`<div class="racha-badge ${{cls}}">${{icon}} ${{txt}}</div>`;
  }}

  document.getElementById('modalContent').innerHTML=`
    <div class="modal-name">${{p.nombre_completo}}</div>
    <div class="modal-meta">
      <span>📌 ${{p.grupo_actual}}</span>
      <span>🏷️ ${{p.tipo_grupo||'-'}}</span>
      <span>👤 ${{p.rol||'Sin rol'}}</span>
      <span>🎓 ${{p.tipo_miembro||'No miembro'}}</span>
      ${{p.at_risk?'<span class="badge badge-riesgo">En riesgo</span>':''}}
    </div>
    ${{rachaHtml}}
    <div class="modal-stats">
      <div class="modal-stat">
        <div class="modal-stat-val" style="color:${{pctColor(p.pct_q1)}}">${{p.pct_q1}}%</div>
        <div class="modal-stat-lbl">Q1 (${{p.asist_q1}}/${{p.total_q1}})</div>
        ${{p.status_q1?`<div style="margin-top:4px">${{badgeHtml(p.status_q1)}}</div>`:''}}
      </div>
      <div class="modal-stat">
        <div class="modal-stat-val" style="color:${{pctColor(p.pct_q2)}}">${{p.pct_q2}}%</div>
        <div class="modal-stat-lbl">Q2 (${{p.asist_q2}}/${{p.total_q2}})</div>
        ${{p.status_q2?`<div style="margin-top:4px">${{badgeHtml(p.status_q2)}}</div>`:''}}
      </div>
      <div class="modal-stat">
        <div class="modal-stat-val" style="color:${{pctColor(p.pct_total)}}">${{p.pct_total}}%</div>
        <div class="modal-stat-lbl">Total (${{p.total_asistencias}}/${{p.total_sesiones}})</div>
        <div style="margin-top:4px">${{badgeHtml(p.status)}}</div>
      </div>
    </div>
    <div class="timeline-title">Historial <span style="font-size:12px;font-weight:400;color:var(--text-muted)">✓ asistio · ✗ falto · * evento</span></div>
    <div class="timeline" id="modalTL"></div>
    <canvas id="modalChart" height="100"></canvas>
  `;

  document.getElementById('modalTL').innerHTML=p.sesiones.map(s=>{{
    const cls=s.evento?'evento':s.asistio?'asistio':'falto';
    const icon=s.asistio?'✓':'✗';
    const lbl=s.evento?fmtDate(s.fecha)+' '+s.evento:fmtDate(s.fecha);
    const qStyle=s.quarter==='Q2'?'outline:2px solid #10B98130;outline-offset:-2px':'';
    return`<div class="tl-dot ${{cls}}" style="${{qStyle}}">${{icon}}<span class="tl-label">${{fmtDate(s.fecha)}}</span><span class="tt">${{lbl}}</span></div>`;
  }}).join('');

  if(drillChart)drillChart.destroy();
  drillChart=new Chart(document.getElementById('modalChart'),{{
    type:'bar',
    data:{{labels:['Q1','Q2','Total'],datasets:[{{data:[p.pct_q1,p.pct_q2,p.pct_total],
      backgroundColor:['#4F46E599','#10B98199','#6B728099'],borderRadius:6}}]}},
    options:{{responsive:true,plugins:{{legend:{{display:false}}}},
      scales:{{y:{{min:0,max:100,ticks:{{callback:v=>v+'%'}}}}}}
    }}
  }});
  document.getElementById('modalOverlay').classList.add('open');
}}

// ── GROUP DRILLDOWN ────────────────────────────────────────────────────────
function openGroupDrilldown(groupName){{
  const members=DATA.personas.filter(p=>p.grupo_actual===groupName);
  if(!members.length)return;
  const g=DATA.grupos.find(x=>x.nombre===groupName)||{{}};
  const sd=g.status_dist||{{}};

  // Compute group-specific evolution
  const dateSet=new Set(members.flatMap(m=>m.sesiones.map(s=>s.fecha)));
  const dates=[...dateSet].sort();
  const gEv=dates.map(fecha=>{{
    const tot=members.filter(m=>m.sesiones.some(s=>s.fecha===fecha)).length;
    const att=members.filter(m=>m.sesiones.some(s=>s.fecha===fecha&&s.asistio)).length;
    const evento=(DATA.eventos||{{}})[fecha]||null;
    return{{fecha,tot,att,pct:tot>0?Math.round(att/tot*100):0,evento}};
  }});

  // Bottom 5 by attendance
  const bottom5=[...members].sort((a,b)=>a.pct_total-b.pct_total).slice(0,5);

  document.getElementById('modalContent').innerHTML=`
    <div class="modal-name">${{groupName}}</div>
    <div class="modal-meta">
      <span>🏷️ ${{g.tipo_grupo||'-'}}</span>
      <span>👥 ${{members.length}} personas</span>
      <span>📅 ${{dates.length}} sesiones</span>
    </div>
    <div class="modal-stats-4">
      <div class="modal-stat"><div class="modal-stat-val" style="color:#10B981">${{sd.Fiel||0}}</div><div class="modal-stat-lbl">Fieles</div></div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:#4F46E5">${{sd.Activo||0}}</div><div class="modal-stat-lbl">Activos</div></div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:#F59E0B">${{sd.Inconstante||0}}</div><div class="modal-stat-lbl">Inconstantes</div></div>
      <div class="modal-stat"><div class="modal-stat-val" style="color:#EF4444">${{sd.Inactivo||0}}</div><div class="modal-stat-lbl">Inactivos</div></div>
    </div>
    <div class="timeline-title">Evolucion del grupo</div>
    <div style="height:160px;margin-bottom:20px"><canvas id="modalChart"></canvas></div>
    <div class="timeline-title">Menor asistencia (click para ver detalle)</div>
    <div style="overflow-x:auto">
      <table class="mini-table">
        <thead><tr><th>Nombre</th><th>% Total</th><th>Status</th></tr></thead>
        <tbody id="groupMembersTbody"></tbody>
      </table>
    </div>
  `;

  document.getElementById('groupMembersTbody').innerHTML=bottom5.map(p=>{{
    return`<tr class="clickable" data-nombre="${{p.nombre_completo}}" onclick="openDrilldown(this.dataset.nombre)">
      <td><strong>${{p.nombre_completo}}</strong></td>
      <td>${{pctBar(p.pct_total)}}</td>
      <td>${{badgeHtml(p.status)}}</td>
    </tr>`;
  }}).join('');

  if(drillChart)drillChart.destroy();
  drillChart=new Chart(document.getElementById('modalChart'),{{
    type:'line',
    data:{{
      labels:gEv.map(e=>fmtDate(e.fecha)+(e.evento?' *':'')),
      datasets:[{{label:'% Asist.',data:gEv.map(e=>e.pct),
        borderColor:'#4F46E5',backgroundColor:'#4F46E520',tension:.3,fill:true,pointRadius:5,
        pointBackgroundColor:gEv.map(e=>e.evento?'#F59E0B':'#4F46E5'),
        pointBorderColor:gEv.map(e=>e.evento?'#D97706':'#3730A3')}}]
    }},
    options:{{responsive:true,maintainAspectRatio:false,...TOUCH,
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{
        title:c=>{{const e=gEv[c[0].dataIndex];return fmtDate(e.fecha)+(e.evento?' - '+e.evento:'')}},
        label:c=>` ${{c.parsed.y}}% (${{gEv[c.dataIndex].att}}/${{gEv[c.dataIndex].tot}})`
      }}}}}},
      scales:{{y:{{min:0,max:100,ticks:{{callback:v=>v+'%'}}}},x:{{grid:{{display:false}}}}}}
    }}
  }});
  document.getElementById('modalOverlay').classList.add('open');
}}

// ── MODAL CLOSE ────────────────────────────────────────────────────────────
function closeModal(e){{if(e.target===document.getElementById('modalOverlay'))closeModalDirect();}}
function closeModalDirect(){{
  document.getElementById('modalOverlay').classList.remove('open');
  if(drillChart){{drillChart.destroy();drillChart=null;}}
}}

// ── INIT ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{{
  const d=DATA.generated_at?new Date(DATA.generated_at):new Date();
  document.getElementById('lastUpdated').textContent=
    'Actualizado: '+d.toLocaleString('es-PE',{{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}});

  renderKPIs();
  renderChartGrupos();
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

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] dashboard.html generado en: {OUTPUT_PATH}")
    if not os.getenv("CI"):
        print("[...] Abriendo en el browser...")
        webbrowser.open(OUTPUT_PATH.as_uri())


if __name__ == "__main__":
    main()
