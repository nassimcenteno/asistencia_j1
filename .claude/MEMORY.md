# MEMORY — Reporte Asistencia J1

> Lee este archivo al inicio de cada sesión para tener contexto completo del proyecto.
> Este archivo es la **memoria oficial y versionada del proyecto** (ver `CLAUDE.md` → "Project Memory"). Tiene prioridad sobre cualquier memoria personal entre sesiones si ambas difieren. Actualízalo constantemente — no solo cuando el usuario lo pida — tras cambios de estructura, reglas de negocio, o bugs/aprendizajes relevantes.

## Contexto
Automatización del control de asistencia semanal del grupo J1 (jóvenes) de la Alianza de Monterrico, Lima, Perú.
Pipeline: Google Sheets → Python → HTML dashboard → GitHub Pages.
Se genera automáticamente los **lunes y martes 9am Lima** via GitHub Actions.
**URL pública:** https://nassimcenteno.github.io/asistencia_j1/

---

## Estructura del proyecto (WAT Framework)

```
config/                        ← Credenciales (gitignored, NUNCA subir)
  service_account.json         ← Auth local para Google Sheets (sin browser)
  (credentials.json y token.json OAuth legacy eliminados 2026-07 — ya no se usaban)

tools/                         ← Scripts Python deterministas
  fetch_sheets_data.py         ← Google Sheets → .tmp/asistencia_raw.json
  process_data.py              ← Reglas de negocio → .tmp/asistencia_processed.json
  generate_dashboard.py        ← ~40 líneas: inyecta el JSON en el template → .tmp/dashboard.html
  dashboard_template.html      ← TODA la UI (HTML/CSS/JS). Marcador __ASISTENCIA_DATA__ = const DATA
  run_report.py                ← Orquestador: corre fetch → process → generate en secuencia

subagents/sub_insights/        ← Sub-agente de análisis profundo (a demanda)
  analyze.py                   ← Lee asistencia_processed.json → reports/insights_report_YYYY-MM-DD.md/.html

workflows/                     ← SOPs en Markdown
  lineamientos_reporte.md      ← REGLAS DE NEGOCIO (leer antes de tocar process_data.py)
  generar_reporte_asistencia.md ← Guía técnica del pipeline + features del dashboard
  analizar_insights.md         ← SOP del sub-agente sub_insights

.tmp/                          ← Archivos intermedios (gitignored)
  asistencia_raw.json
  asistencia_processed.json
  dashboard.html
  .gitkeep                     ← Mantiene la carpeta en git

.github/workflows/reporte.yml  ← GitHub Actions (schedule lunes+martes 14:00 UTC)
.env                           ← SHEET_ID, SHEET_NAME (gitignored)
```

**Nota:** `skills/` se menciona en `CLAUDE.md` como concepto pero no existe en disco (se eliminó `skills/DESIGN_SKILL.md` en 2026-07). Si se necesitan estándares de UI/UX para el dashboard, recrear `skills/` con el documento correspondiente.

---

## Inventario de scripts

| Script | Input | Output | Uso |
|---|---|---|---|
| `fetch_sheets_data.py` | Google Sheets (SA o env var) | `asistencia_raw.json` | Paso 1 |
| `process_data.py` | `asistencia_raw.json` | `asistencia_processed.json` | Paso 2 |
| `generate_dashboard.py` + `dashboard_template.html` | `asistencia_processed.json` | `dashboard.html` | Paso 3 |
| `run_report.py` | — | Corre los 3 en secuencia | Uso local |

**Editar el dashboard = editar `tools/dashboard_template.html`** (HTML/CSS/JS normal, sin llaves duplicadas). `generate_dashboard.py` solo hace `template.replace("__ASISTENCIA_DATA__", json)`.

**Ejecución local:** `python tools/run_report.py`

---

## Configuración crítica

- **Auth local:** `config/service_account.json` — gitignored, nunca subir
- **Auth CI:** secreto `GOOGLE_CREDENTIALS` en GitHub → Settings → Secrets → Actions
- **Sheet ID:** `1-bEJnaHTVpQjZ2E0HQv1IZh8Hf91Jrh4nMViMS69XlE`
- **Sheet Name:** `03. Asistencia_Reporting`
- **Repo GitHub:** https://github.com/nassimcenteno/asistencia_j1

---

## Reglas de negocio

**Ver `workflows/lineamientos_reporte.md`** — fuente de verdad para:
- Status: Fiel ≥80% / Activo 51-79% / Inconstante 1-50% / Inactivo 0%
- Períodos: Q1 ene-mar / Q2 abr-**jul** / Q3 ago-TBD (3 quarters desde 2026-09; `get_quarter()` de 3 ramas). Todo el pipeline expone `pct_q1/q2/q3`, `asist_q*`, `total_q*`, `status_q*`.
- Excepciones de fechas por grupo (denominador del %)
- Eventos especiales (JADAK, Montecamp, Reencuentro, Apologética, El Viaje, Puentes)
- Grupos regidos por asistencia (`ATTENDANCE_DRIVEN_GROUPS` = GDC BETTA, GDC BETTA VIAJEROS): fecha con 0 asistentes ⇒ no hubo sesión (dinámico/retroactivo). Reemplazó al viejo hold `GROUP_END_DATES` y a las excepciones manuales de BETTA. Ver `lineamientos_reporte.md` §12
- En Riesgo: 0 asistencias en las últimas 4 sesiones del grupo (dinámico)
- Racha actual: semanas consecutivas asistiendo (positivo) o ausente (negativo)
- Membresía formal: `Miembro Bautizado` o `Transferido`

### Arquitectura de 3 niveles (desde 2026-07)

El pipeline separa 3 cálculos independientes — ver sección 10 de `lineamientos_reporte.md`:

| Nivel | Aplica `GROUP_START_DATES` | Campo en el JSON |
|---|---|---|
| **Persona** (%, historial, racha, at_risk) | NO — solo su propia `FECHA_INGRESO` | `sesiones`, `total_sesiones` |
| **Grupo** (tabla de grupos, modal de grupo) | SÍ | `sesiones_grupo`, `grupos[].sesiones_totales` |
| **Global** (evolución semanal) | NO — bottom-up desde personas | `evolucion` |

**Por qué:** el Sheet solo tiene `GRUPO_ACTUAL` (grupo de hoy), no histórico por fecha. Aplicarle `GROUP_START_DATES` a una persona que fue reasignada a un grupo nuevo/renombrado le borraría asistencia real de antes del cambio.

**Cuidado al tocar el dashboard:** el modal de grupo (`renderGroupModal` en `dashboard_template.html`) debe usar `sesiones_grupo`, no `sesiones` — usar el campo equivocado ahí fue un bug real (mostraba 18 sesiones en vez de 8 para GDC OMEGA).

**Riesgo conocido:** `GROUP_START_DATES`/`ATTENDANCE_DRIVEN_GROUPS`/`EXCEPTIONS` matchean por nombre de grupo (texto libre, sin ID estable). Si el Sheet renombra un grupo, la regla se desactiva **sin error** — pasó con GDC NEW BETTA → GDC OMEGA (2026-07).

### Filtro de entrada: `GRUPO_ACTUAL` en blanco

`process_data.py` descarta **toda fila** cuya columna `GRUPO_ACTUAL` venga vacía (`if not grupo_actual: continue`, ~línea 182). Consecuencia: una persona sin grupo asignado **no existe** para el pipeline — no aparece en KPIs, tablas, dashboard ni sub-agente, sin importar su `ROL_ACTUAL` ni `TIPO_MIEMBRO`. Los **mentores activos sin grupo** (gente entre asignaciones) quedan fuera por esto — no es un bug ni una regresión, siempre fue así. Si se quiere mostrarlos hay que cambiar la regla explícitamente (ej. bucket "sin grupo" que no afecte métricas por grupo, decidir si cuentan en KPIs globales).

### Denominador semanal (`total_aplica` en `evolucion`)

No es "toda la gente con `GRUPO_ACTUAL`". Por cada fecha excluye además: (1) miembros de grupos `ATTENDANCE_DRIVEN_GROUPS` en fechas donde ese grupo tuvo 0 asistentes, y (2) personas con `FECHA_INGRESO` posterior a esa fecha. Por eso el denominador de una semana puede ser menor que el total de personas activas.

### Fuente: pestaña vs. "maestro"

El pipeline lee la pestaña `03. Asistencia_Reporting` (log largo, una fila por persona×fecha). El usuario tiene además un "maestro" (roster, una fila por persona). Los conteos pueden no cuadrar (histórico: 309 pipeline vs 312 maestro) si la pestaña de reporting va atrasada respecto al maestro. Además el número baila entre corridas porque el Sheet cambia en vivo (gente cargando asistencia); a 2026-09-10 el pipeline marca ~294.

---

## Features del dashboard (estado actual)

- **Filtro global de período** (chips Q1/Q2/Q3 combinables, arriba a la derecha de las pestañas): recalcula KPIs, ranking, evolución, tabla/ranking de grupos, tabla de personas y CSV para los quarters seleccionados. **Con los 3 Q activos los helpers `scoped*()` devuelven `DATA.*` sin tocar** → el default es byte-idéntico a antes del filtro (el conteo de personas NO se mueve). Excepciones: la dona por tipo es solo poblacional (no obedece), "En Riesgo" es global (solo el % por fila obedece), la matriz de status tiene su propio selector, y "Participantes"/"% membresía" quedan sobre el roster completo. `process_data.py` expone `asist_qN`/`posibles_qN`/`sesiones_qN` por grupo para combinar con sumas.
- **Filtro de período local en los modales** (`modalQBar()` + `modalQ` Set): el pop-up de persona y el de grupo tienen chips Q propios, independientes del global, que arrancan copiando el estado global. `openDrilldown`/`openGroupDrilldown` = setup; `renderPersonModal()`/`renderGroupModal()` arman el cuerpo y se re-ejecutan al togglear (`toggleModalQ`).
- KPIs globales + delta week-over-week (↑↓ vs semana anterior)
- 4 tabs: Resumen / Grupos / Personas / Riesgo
- Gráficos: barras por grupo, dona por tipo, evolución semanal, comparativa Q1/Q2/Q3 por grupo
- Tablas ordenables por cualquier columna + filtros + búsqueda + exportar CSV (tabla Personas tiene columnas Q1%/Q2%/Q3%)
- Modal persona: racha 🔥/❄️, historial visual por sesión, mini-chart Q1/Q2/Q3/Total
- Modal grupo: evolución del grupo + ranking de menor asistencia (clickeable)
- "Hace N semanas" en lista de riesgo
- KPI cards navegables → filtran la tabla correspondiente
- Matriz de transición de status con **selector de transición** (Q1→Q2 / Q2→Q3 / Q1→Q3), se recalcula client-side desde `status_q*` (el `status_matrix` que emitía `process_data.py` se eliminó por muerto)
- **Responsive mobile (rediseño 2026-09-11):** en Personas/Riesgo/Grupos, cada `<tr>` lleva una celda extra `.mrow` (oculta en desktop vía `.tbl td.mrow{display:none}`) con una tarjeta compacta a medida — nombre+status arriba, línea de contexto, barra de %; Grupos además stats + chips de composición. Reemplaza el patrón viejo de listar cada columna como fila "ETIQUETA: valor" (7-11 filas por tarjeta, ilegible). Los `<td data-label="...">` de escritorio se ocultan con `display:none` en `@media(max-width:640px)` en vez de convertirse en filas. El gráfico "Comparativa por Quarter por Grupo" (Grupos) pasa a barras horizontales en mobile (`plotOptions.bar.horizontal` + swap de `xaxis`/`yaxis` — con horizontal:true, Apex le pega el formatter de `%` a los NOMBRES si se lo dejás en yaxis) en vez de forzar scroll horizontal, que se sentía "cortado" sin ninguna pista de que se podía deslizar (mismo motivo por el que el filtro/KPI grid de 7 tarjetas **no** usa scroll-carousel: la última tarjeta huérfana pasa a `grid-column:1/-1` en vez de scrollear). La pestaña Resumen (KPIs, donut, evolución semanal) quedó **deliberadamente sin este rediseño** — el usuario prefirió el diseño ya commiteado ahí; ese diseño tiene un bug mobile preexistente y conocido (no introducido por este cambio): a ≤640px la card "Ranking de grupos" desborda ~64px por el `min-width:auto` por defecto de los ítems de `.charts-2col` (CSS grid) — pendiente si se decide tocar Resumen en el futuro. Modal → bottom sheet, tabs con iconos.
- **Dark mode con tokens de color propios:** `--accent/--pos/--warn/--neg` (+ variantes `-soft`/`-ink`) en `:root`/`.dark`, en vez de hexadecimales sueltos repetidos por todo el HTML/JS. En dark, `--accent` se aclara a `#818CF8` y `--neg` a `#F87171` — los tonos "500" de light (`#4F46E5`, `#EF4444`) quedan con ~2.3:1 y ~3.75:1 de contraste sobre `--surface` oscuro (invisibles/al límite); `--pos`/`--warn` sí pasan AA en dark sin cambiar. Badges/timeline/matriz/racha usan pares `-soft`/`-ink` (fondo tintado oscuro + texto claro, mismo patrón que ya tenía `.alert-strip`). Los charts de ApexCharts resuelven color con `cssVar('--nombre')` en cada render (no en el objeto `Q_META`/config estático) porque `toggleDark()` ahora **re-renderiza todo** (`refreshAfterThemeChange()`) — si no, los colores quedaban calculados para el tema anterior hasta el próximo cambio de filtro. También se fijó `chart.background:'transparent'` en `baseChartOpts()` (Apex pintaba su propio gris de tema oscuro por defecto, quedaba una caja desencajada dentro de la card).

---

## Limpieza estructural (2026-09-10)

- **`generate_dashboard.py`: 1255 → ~50 líneas.** La UI se extrajo a `tools/dashboard_template.html` (archivo HTML real, sin `{{`/`}}`). El generador solo inyecta el JSON en el marcador `__ASISTENCIA_DATA__` (valida que aparezca exactamente 1 vez). Se verificó que el `dashboard.html` de salida quedó **byte-idéntico**. Toda referencia a funciones JS del dashboard en el changelog de abajo (`MATRIX_TRANS`, `renderGroupModal`, `scopedPersonas`, etc.) hoy vive en `dashboard_template.html`, no en `generate_dashboard.py`.
- **`process_data.py`:** se eliminó `get_active_from()` (era `return ingreso`, identidad muerta) y el alias `group_af_map` (se usa `GROUP_START_DATES` directo); `"excepciones"` salió del JSON de salida (nadie lo consumía, como pasó con `status_matrix`); `evolucion` calcula asistentes por fecha con un `Counter` en un solo recorrido en vez de re-escanear personas por cada fecha; `build_historial` computa `iso` una vez.
- **`analyze.py`:** se eliminó `top_riesgo` (variable muerta) y el `_mr_dict` del tuple de `mom_reciente`.
- **`dashboard_template.html`:** se quitó el bloque vacío `if(page==='riesgo'){}` de `navToStatus`.
- **`requirements.txt`:** se quitó `google-auth-oauthlib` (era para el flujo OAuth que se eliminó en 2026-07; hoy solo se usa Service Account).

---

## Aprendizajes técnicos

| Fecha | Aprendizaje |
|---|---|
| 2026-05 | Service Account en vez de OAuth para auth sin browser en CI |
| 2026-05 | `CI=true` en GitHub Actions → guard para no abrir browser |
| 2026-05 | GitHub Pages source "GitHub Actions" se auto-configura sin botón Save |
| 2026-05 | Push de workflow files requiere PAT con scope `workflow` |
| 2026-05 | Backslashes en regex dentro de f-strings Python generan regex rotas en JS → usar `data-nombre` + `this.dataset.nombre` para onclick seguros |
| 2026-05 | VSCode HTML preview bloquea CDN/JS → siempre probar en Chrome/Edge |
| 2026-07 | Separación persona/grupo/global (ver arriba) — refactor grande, verificado con diff exacto del JSON de salida antes/después de limpiar el código |
| 2026-07 | `process_data.py` limpiado: sin imports muertos, sin detecciones de columna sin uso (`apellido`, `status_raw`, `grupo` histórica), `grupos_stats` y totales por persona en un solo paso en vez de múltiples list comprehensions redundantes |
| 2026-07 | Limpieza de repo: `skills/DESIGN_SKILL.md` eliminado y commiteado; `config/credentials.json` y `config/token.json` (OAuth legacy, nunca trackeados en git, sin referencias en código) borrados localmente. `CLAUDE.md` formaliza este archivo (`.claude/MEMORY.md`) como memoria oficial del proyecto |
| 2026-07 | Reorg de grupos en el Sheet: `GDA USIL [TBD]` → `GDA USIL` (rename simple, sin código hardcodeado que tocar). `GDC EPSILON` y `GDA FAITH` se disolvieron intencionalmente, miembros repartidos en otros grupos. Grupos nuevos `GDC ETA` y `GDA ULIMA` formados con gente antigua de J1 → por decisión del usuario, NO llevan entrada en `GROUP_START_DATES` (a diferencia de LAMBDA/OMEGA que sí la llevan por ser cohortes nuevas). Detalle completo en `workflows/lineamientos_reporte.md` → Historial de cambios |
| 2026-07-23 | Eventos EJEC (11/07) y Reencuentro EJEC (18/07) agregados a `EVENTS` en `process_data.py`. Nota: esas dos fechas habían mostrado asistencia casi nula en un fetch anterior porque la mayoría de los grupos aún no habían cargado su asistencia al Sheet en ese momento — no era un problema real, solo datos incompletos al momento del fetch (ver denominador semanal en "Reglas de negocio") |
| 2026-09-10 (2) | Filtro global de período (multi-select Q1/Q2/Q3) en el dashboard — ver "Features". Helpers JS `scopedPersonas()`/`scopedGrupos()`/`scopedGlobalPct()` (con short-circuit `if(isAllQ()) return DATA.*`) + `pAsist/pTotal/pPct/pStatus` y `gAsist/gPosibles/gPct` (todos con 2º arg `qs=QSEL`); `applyGlobalQ()` re-renderiza al togglear. La dona por tipo quedó estática (poblacional). Eventos J-Fest (15/08) y Alaba (05/09). Rediseño del chart de evolución del modal de grupo (igual al de evolución total) y quitado el eje Y del mini-chart Q por persona. `filterGrupoQ` eliminado (redundante). |
| 2026-09-10 (3) | Filtro de período LOCAL en los pop-ups (`modalQBar()`, `modalQ`, `toggleModalQ`, `modalState`). `openDrilldown`/`openGroupDrilldown` → setup; cuerpo en `renderPersonModal()`/`renderGroupModal()`. Persona: 4ª tarjeta pasa a ser la selección combinada (label `qShort(modalQ)`, ej. "Q2+Q3"), historial y mini-chart filtrados. Grupo: status cards, N sesiones, chart de evolución y bottom-5 recalculados al `modalQ`. Verificado: conteo 294 estable en todos los estados del filtro global; `series.data` del mini-chart correcto para combos; sin errores JS. |
| 2026-09-10 (4) | **GDC BETTA y GDC BETTA VIAJEROS → regla de asistencia** (`ATTENDANCE_DRIVEN_GROUPS` + `group_had_session()` sobre el mapa `group_attendance`): fecha con 0 asistentes ⇒ no hubo sesión (dinámico, retroactivo). Se eliminó `GROUP_END_DATES`/`session_before_group_end()` (el hold de BETTA VIAJEROS desde 27/6) y las 4 excepciones manuales de BETTA (02/05, 23/05, 30/05, 06/06). **04/07 (LAMBDA + SIGMA) NO se tocó** — sigue como fecha explícita en `EXCEPTIONS`. El marcado de `aplica_denominador`/`aplica_grupo` pasó del loop de filas a un post-proceso (necesita el mapa de asistencia completo). Efecto: BETTA VIAJEROS 16→17 sesiones, BETTA 23→22. Dashboard sin cambios (solo presenta lo que calcula `process_data.py`). |
| 2026-09-10 | **Q3 agregado.** Q2 dejó de ser "abril en adelante" y ahora es abr–jul; Q3 = ago–TBD. `get_quarter()` en `process_data.py` pasó a 3 ramas y la lógica per-quarter se generalizó a dicts `asist_q`/`total_q`/`pct_q` keyed por `QUARTERS=["Q1","Q2","Q3"]` (persona y grupo). Dashboard: columna Q3% en tabla Personas, 3ª serie en el chart comparativo, opción Q3 en filtro de grupos, 4ª tarjeta + mini-chart en modal de persona, y **selector de transición** en la matriz de status (Q1→Q2 / Q2→Q3 / Q1→Q3, `MATRIX_TRANS` en `generate_dashboard.py`). `sub_insights/analyze.py`: semáforo con Q3% y Δ Q2→Q3, Momentum con dos matrices (helper `momentum_counts`), titulares usan la transición más reciente con datos. Se borró el `status_matrix` del JSON de `process_data.py` — código muerto (nadie lo consumía). Verificado con render headless de las 3 pestañas. |
| 2026-07-24 | Limpieza en el Sheet: 15 miembros inactivos de `GDC SIGMA` (0% asistencia todo el ciclo, racha -20) dados de baja del grupo — `GRUPO_ACTUAL` y `ROL_ACTUAL` puestos en blanco → salen del pipeline. Además 4 mentores que ya estaban sin grupo (incluido el owner) perdieron su `ROL_ACTUAL` de "Mentor". Ninguno de esos 4 aparecía en el dashboard antes tampoco (ver "Filtro de entrada: `GRUPO_ACTUAL` en blanco"). El conteo total de personas bajó a 309; el maestro del usuario marca 312 (posible desfase entre pestañas) |
