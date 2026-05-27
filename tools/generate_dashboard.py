"""
Tool: generate_dashboard.py
Genera dashboard.html a partir de .tmp/asistencia_processed.json y lo abre en el browser.
"""

import json
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"
OUTPUT_PATH = ROOT / "dashboard.html"


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
.last-updated{{font-size:12px;color:var(--text-muted)}}
.container{{max-width:1400px;margin:0 auto;padding:24px 32px}}
.tabs{{display:flex;gap:4px;background:var(--border);padding:4px;border-radius:8px;margin-bottom:24px;width:fit-content}}
.tab{{padding:8px 20px;border-radius:6px;border:none;background:transparent;cursor:pointer;font-size:14px;font-weight:500;color:var(--text-muted);transition:all .15s}}
.tab.active{{background:var(--card);color:var(--primary);box-shadow:var(--shadow)}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}}
.kpi-card{{background:var(--card);border-radius:var(--radius);padding:20px;border:1px solid var(--border);box-shadow:var(--shadow);transition:transform .15s}}
.kpi-card:hover{{transform:translateY(-2px);box-shadow:var(--shadow-lg)}}
.kpi-label{{font-size:12px;font-weight:500;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px}}
.kpi-value{{font-size:32px;font-weight:800;margin-top:6px}}
.kpi-value.fiel{{color:var(--success)}} .kpi-value.activo{{color:var(--primary)}}
.kpi-value.inconstante{{color:var(--warning)}} .kpi-value.inactivo{{color:var(--danger)}}
.kpi-value.riesgo{{color:#DC2626}}
.kpi-sub{{font-size:12px;color:var(--text-muted);margin-top:4px}}
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
table{{width:100%;border-collapse:collapse}}
th{{padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border);background:var(--bg)}}
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
.modal-close{{position:absolute;top:16px;right:16px;width:32px;height:32px;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;color:var(--text-muted)}}
.modal-close:hover{{background:var(--border)}}
.modal-name{{font-size:22px;font-weight:800;margin-bottom:4px}}
.modal-meta{{font-size:13px;color:var(--text-muted);margin-bottom:20px}}
.modal-meta span{{margin-right:16px}}
.modal-stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}}
.modal-stat{{background:var(--bg);border-radius:8px;padding:12px;text-align:center}}
.modal-stat-val{{font-size:22px;font-weight:800}}
.modal-stat-lbl{{font-size:11px;color:var(--text-muted);margin-top:2px}}
.timeline-title{{font-size:14px;font-weight:600;margin-bottom:10px}}
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
@media(max-width:768px){{.charts-grid{{grid-template-columns:1fr}}.container{{padding:16px}}.header{{padding:12px 16px}}}}
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
    <button class="tab active" onclick="showPage('overview',this)">Resumen</button>
    <button class="tab" onclick="showPage('grupos',this)">Por Grupo</button>
    <button class="tab" onclick="showPage('riesgo',this)">En Riesgo</button>
    <button class="tab" onclick="showPage('personas',this)">Participantes</button>
  </div>

  <!-- ===== RESUMEN ===== -->
  <div class="page active" id="page-overview">
    <div class="kpi-grid" id="kpiGrid" style="grid-template-columns:repeat(7,1fr)"></div>
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Asistencia por Grupo</div>
        <div style="height:300px"><canvas id="chartGrupos"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Distribucion por Tipo (GBU / GDA / GDC)</div>
        <div style="height:300px"><canvas id="chartTipos"></canvas></div>
      </div>
      <div class="chart-card full">
        <div class="chart-title">Evolucion Semanal — % Asistencia <span style="font-size:12px;font-weight:400;color:var(--text-muted)">(puntos naranjas = eventos unidos)</span></div>
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
        <span class="table-title">Detalle por Grupo</span>
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
        </div>
      </div>
      <table>
        <thead><tr>
          <th>Grupo</th><th>Tipo</th><th>Miembros</th><th>Sesiones</th>
          <th>% Asistencia</th><th>Miembros Formales</th><th>% Membresia</th>
          <th>Fieles</th><th>Activos</th><th>Inconstantes</th><th>Inactivos</th>
        </tr></thead>
        <tbody id="tbodyGrupos"></tbody>
      </table>
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
      ⚠ Personas con <strong>0 asistencias en las ultimas 4 sesiones</strong> (2/5, 9/5, 16/5, 23/5).
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
        </div>
      </div>
      <table>
        <thead><tr>
          <th>Nombre</th><th>Grupo</th><th>Tipo</th><th>% Total</th><th>Status</th><th>Ultima asistencia</th>
        </tr></thead>
        <tbody id="tbodyRiesgo"></tbody>
      </table>
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
        </div>
      </div>
      <table>
        <thead><tr>
          <th>Nombre</th><th>Grupo</th><th>Tipo</th><th>Rol</th>
          <th>Q1%</th><th>Q2%</th><th>Total%</th><th>Status</th>
        </tr></thead>
        <tbody id="tbodyPersonas"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- Modal drilldown -->
<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
  <div class="modal">
    <button class="modal-close" onclick="closeModalDirect()">x</button>
    <div id="modalContent"></div>
  </div>
</div>

<script>
const DATA = {data_json};

// ── utils ──────────────────────────────────────────────────────────
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

// ── navigation ─────────────────────────────────────────────────────
function showPage(name,btn){{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  btn.classList.add('active');
}}

// ── KPIs ───────────────────────────────────────────────────────────
function renderKPIs(){{
  const k=DATA.kpis, sd=k.status_dist||{{}};
  document.getElementById('kpiGrid').innerHTML=[
    {{l:'Total Participantes',v:k.total_personas,sub:'con grupo activo'}},
    {{l:'% Asistencia Global',v:k.pct_asistencia_global+'%',sub:'promedio general'}},
    {{l:'Fieles',v:sd.Fiel||0,c:'fiel',sub:'80%+ asistencia'}},
    {{l:'Activos',v:sd.Activo||0,c:'activo',sub:'50-79%'}},
    {{l:'Inconstantes',v:sd.Inconstante||0,c:'inconstante',sub:'1-50%'}},
    {{l:'Inactivos',v:sd.Inactivo||0,c:'inactivo',sub:'0%'}},
    {{l:'En Riesgo',v:k.total_at_risk||0,c:'riesgo',sub:'0 asist. en 4 semanas'}},
  ].map(c=>`<div class="kpi-card"><div class="kpi-label">${{c.l}}</div><div class="kpi-value ${{c.c||''}}">${{c.v}}</div><div class="kpi-sub">${{c.sub}}</div></div>`).join('');
  // riesgo page kpis
  document.getElementById('kpiRiesgo').textContent=k.total_at_risk||0;
  document.getElementById('kpiTotal').textContent=k.total_personas;
}}

// ── chart: grupos barras horizontales ─────────────────────────────
function renderChartGrupos(){{
  const g=DATA.grupos.slice(0,14);
  new Chart(document.getElementById('chartGrupos'),{{
    type:'bar',
    data:{{
      labels:g.map(x=>x.nombre),
      datasets:[{{label:'% Asistencia',data:g.map(x=>x.pct_asistencia),
        backgroundColor:g.map(x=>pctColor(x.pct_asistencia)+'CC'),
        borderColor:g.map(x=>pctColor(x.pct_asistencia)),borderWidth:1,borderRadius:5}}]
    }},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>` ${{c.parsed.x}}%`}}}}}},
      scales:{{x:{{min:0,max:100,grid:{{color:'#F3F4F6'}},ticks:{{callback:v=>v+'%'}}}},y:{{grid:{{display:false}}}}}}
    }}
  }});
}}

// ── chart: tipos dona ──────────────────────────────────────────────
function renderChartTipos(){{
  const t=DATA.tipos;
  new Chart(document.getElementById('chartTipos'),{{
    type:'doughnut',
    data:{{
      labels:t.map(x=>`${{x.tipo}} - ${{x.label}}`),
      datasets:[{{data:t.map(x=>x.personas),
        backgroundColor:['#4F46E5CC','#10B981CC','#F59E0BCC','#EF4444CC'],borderWidth:2,borderColor:'#fff'}}]
    }},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{position:'bottom'}},tooltip:{{callbacks:{{label:c=>` ${{c.label}}: ${{c.parsed}} personas`}}}}}}
    }}
  }});
}}

// ── chart: evolucion con eventos destacados ───────────────────────
function renderChartEvolucion(){{
  const ev=DATA.evolucion;
  new Chart(document.getElementById('chartEvolucion'),{{
    type:'line',
    data:{{
      labels:ev.map(e=>fmtDate(e.fecha)+(e.evento?' *':'')),
      datasets:[{{
        label:'% Asistencia',data:ev.map(e=>e.pct),
        borderColor:'#4F46E5',backgroundColor:'#4F46E520',
        tension:.3,fill:true,pointRadius:6,
        pointBackgroundColor:ev.map(e=>e.evento?'#F59E0B':'#4F46E5'),
        pointBorderColor:ev.map(e=>e.evento?'#D97706':'#3730A3'),
        pointBorderWidth:ev.map(e=>e.evento?2:1),
      }}]
    }},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{
        title:c=>{{const e=ev[c[0].dataIndex];return fmtDate(e.fecha)+(e.evento?' - '+e.evento:'')}},
        label:c=>` ${{c.parsed.y}}% (${{'asistentes: '}}${{ev[c.dataIndex].asistentes}})`
      }}}}}},
      scales:{{y:{{min:0,max:100,grid:{{color:'#F3F4F6'}},ticks:{{callback:v=>v+'%'}}}},x:{{grid:{{display:false}}}}}}
    }}
  }});
}}

// ── chart: Q1 vs Q2 ───────────────────────────────────────────────
function renderChartQ1Q2(){{
  const g=DATA.grupos;
  new Chart(document.getElementById('chartQ1Q2'),{{
    type:'bar',
    data:{{
      labels:g.map(x=>x.nombre),
      datasets:[
        {{label:'Q1 (Ene-Mar)',data:g.map(x=>x.pct_q1),backgroundColor:'#4F46E599',borderRadius:4}},
        {{label:'Q2 (Abr+)',data:g.map(x=>x.pct_q2),backgroundColor:'#10B98199',borderRadius:4}},
      ]
    }},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{tooltip:{{callbacks:{{label:c=>` ${{c.dataset.label}}: ${{c.parsed.y}}%`}}}}}},
      scales:{{y:{{min:0,max:100,ticks:{{callback:v=>v+'%'}},grid:{{color:'#F3F4F6'}}}},x:{{grid:{{display:false}}}}}}
    }}
  }});
}}

// ── tabla grupos ──────────────────────────────────────────────────
function renderTableGrupos(){{
  const tipo=document.getElementById('filterGrupoTipo').value;
  const q=document.getElementById('filterGrupoQ').value;
  const grupos=DATA.grupos.filter(g=>!tipo||g.tipo_grupo===tipo);
  const sd=g=>g.status_dist||{{}};
  document.getElementById('tbodyGrupos').innerHTML=grupos.map(g=>{{
    const pct=q==='q1'?g.pct_q1:q==='q2'?g.pct_q2:g.pct_asistencia;
    return `<tr>
      <td><strong>${{g.nombre}}</strong></td>
      <td>${{g.tipo_grupo||'-'}}</td>
      <td>${{g.num_miembros}}</td>
      <td>${{g.sesiones_totales}}</td>
      <td>${{pctBar(pct)}}</td>
      <td>${{g.num_miembros_formales}}</td>
      <td><span style="font-weight:600;color:var(--primary)">${{g.pct_membresia}}%</span></td>
      <td><span style="color:#10B981;font-weight:700">${{sd(g).Fiel||0}}</span></td>
      <td><span style="color:#4F46E5;font-weight:700">${{sd(g).Activo||0}}</span></td>
      <td><span style="color:#F59E0B;font-weight:700">${{sd(g).Inconstante||0}}</span></td>
      <td><span style="color:#EF4444;font-weight:700">${{sd(g).Inactivo||0}}</span></td>
    </tr>`;
  }}).join('');
}}

// ── matriz Q1→Q2 ─────────────────────────────────────────────────
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
      let cls=v===0?'m-zero':si===sj?'m-same':sj<si?'m-up':'m-down';
      html+=`<td class="${{cls}}">${{v||'-'}}</td>`;
    }});
    html+='</tr>';
  }});
  document.getElementById('matrixTable').innerHTML=html;
}}

// ── en riesgo ─────────────────────────────────────────────────────
function renderRiesgo(){{
  const tipo=document.getElementById('filterRiesgoTipo').value;
  const lista=(DATA.at_risk||[]).filter(p=>!tipo||p.tipo_grupo===tipo);
  document.getElementById('tbodyRiesgo').innerHTML=lista.map(p=>`
    <tr class="clickable" onclick="openDrilldown('${{p.nombre_completo.replace(/'/g,"\\\\'")}}')" >
      <td><strong>${{p.nombre_completo}}</strong></td>
      <td>${{p.grupo_actual}}</td>
      <td>${{p.tipo_grupo||'-'}}</td>
      <td>${{pctBar(p.pct_total)}}</td>
      <td>${{badgeHtml(p.status)}}</td>
      <td style="color:var(--text-muted)">${{p.ultima_asistencia?fmtDate(p.ultima_asistencia):'Nunca'}}</td>
    </tr>`).join('');
}}

// ── tabla personas ────────────────────────────────────────────────
function renderPersonas(){{
  const search=document.getElementById('searchPersona').value.toLowerCase();
  const grupo=document.getElementById('filterPGrupo').value;
  const tipo=document.getElementById('filterPTipo').value;
  const status=document.getElementById('filterPStatus').value;
  const list=DATA.personas.filter(p=>
    (!search||p.nombre_completo.toLowerCase().includes(search))&&
    (!grupo||p.grupo_actual===grupo)&&
    (!tipo||p.tipo_grupo===tipo)&&
    (!status||p.status===status)
  );
  document.getElementById('tbodyPersonas').innerHTML=list.map(p=>`
    <tr class="clickable" onclick="openDrilldown('${{p.nombre_completo.replace(/'/g,"\\\\'")}}')" >
      <td><strong>${{p.nombre_completo}}</strong></td>
      <td>${{p.grupo_actual}}</td>
      <td>${{p.tipo_grupo||'-'}}</td>
      <td>${{p.rol||'-'}}</td>
      <td style="font-weight:600;color:${{pctColor(p.pct_q1)}}">${{p.pct_q1}}%</td>
      <td style="font-weight:600;color:${{pctColor(p.pct_q2)}}">${{p.pct_q2}}%</td>
      <td>${{pctBar(p.pct_total)}}</td>
      <td>${{badgeHtml(p.status)}}</td>
    </tr>`).join('');
}}

// ── drilldown ─────────────────────────────────────────────────────
let drillChart=null;
function openDrilldown(name){{
  const p=DATA.personas.find(x=>x.nombre_completo===name);
  if(!p)return;
  const miembro=p.tipo_miembro||'No miembro';
  document.getElementById('modalContent').innerHTML=`
    <div class="modal-name">${{p.nombre_completo}}</div>
    <div class="modal-meta">
      <span>📌 ${{p.grupo_actual}}</span>
      <span>🏷️ ${{p.tipo_grupo||'-'}}</span>
      <span>👤 ${{p.rol||'Sin rol'}}</span>
      <span>🎓 ${{miembro}}</span>
      ${{p.at_risk?'<span class="badge badge-riesgo">En riesgo</span>':''}}
    </div>
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
    <div class="timeline-title">Historial de Asistencia <span style="font-size:12px;font-weight:400;color:var(--text-muted)">— * = evento</span></div>
    <div class="timeline" id="modalTL"></div>
    <canvas id="modalChart" height="100"></canvas>
  `;
  const tl=document.getElementById('modalTL');
  tl.innerHTML=p.sesiones.map(s=>{{
    const cls=s.evento?'evento':s.asistio?'asistio':'falto';
    const icon=s.asistio?'✓':'✗';
    const label=s.evento?fmtDate(s.fecha)+' '+s.evento:fmtDate(s.fecha);
    const qBorder=s.quarter==='Q2'?'outline:2px solid #10B98130;outline-offset:-2px':'';
    return `<div class="tl-dot ${{cls}}" style="${{qBorder}}">
      ${{icon}}<span class="tl-label">${{fmtDate(s.fecha)}}</span>
      <span class="tt">${{label}}</span>
    </div>`;
  }}).join('');
  if(drillChart)drillChart.destroy();
  drillChart=new Chart(document.getElementById('modalChart'),{{
    type:'bar',
    data:{{
      labels:['Q1','Q2','Total'],
      datasets:[{{data:[p.pct_q1,p.pct_q2,p.pct_total],
        backgroundColor:['#4F46E599','#10B98199','#6B728099'],borderRadius:6}}]
    }},
    options:{{responsive:true,plugins:{{legend:{{display:false}}}},
      scales:{{y:{{min:0,max:100,ticks:{{callback:v=>v+'%'}}}}}}
    }}
  }});
  document.getElementById('modalOverlay').classList.add('open');
}}
function closeModal(e){{if(e.target===document.getElementById('modalOverlay'))closeModalDirect();}}
function closeModalDirect(){{
  document.getElementById('modalOverlay').classList.remove('open');
  if(drillChart){{drillChart.destroy();drillChart=null;}}
}}

// ── init ──────────────────────────────────────────────────────────
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

  // populate grupo filters
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
    import os
    if not os.getenv("CI"):
        print("[...] Abriendo en el browser...")
        webbrowser.open(OUTPUT_PATH.as_uri())


if __name__ == "__main__":
    main()
