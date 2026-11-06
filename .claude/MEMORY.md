# MEMORY — Reporte Asistencia J1

> Lee este archivo al inicio de cada sesión para tener contexto completo del proyecto.
> Es la **memoria oficial y versionada del proyecto** (ver `CLAUDE.md` → "Project Memory"). Tiene prioridad sobre cualquier memoria personal entre sesiones si ambas difieren. Actualízalo tras cambios de estructura, reglas de negocio o aprendizajes relevantes. Última sincronización completa: **2026-11-06**.

## 1. Contexto

Automatización del control de asistencia semanal del grupo J1 (jóvenes) de la Alianza de Monterrico, Lima, Perú.
Pipeline: Google Sheets → Python → HTML dashboard → GitHub Pages. Se genera solo los **lunes y martes 9am Lima** (GitHub Actions) y a demanda desde la pestaña Actions.

- **URL pública:** https://nassimcenteno.github.io/asistencia_j1/
- **Repo:** https://github.com/nassimcenteno/asistencia_j1 (rama `main`)
- **Idioma de trabajo:** español.

---

## 2. Cómo retomar (checklist de una sesión nueva)

1. Lee este archivo y `workflows/lineamientos_reporte.md` (reglas de negocio, fuente de verdad) antes de tocar `process_data.py` o el dashboard.
2. **Entorno local (Windows):**
   - Python 3.11 instalado por usuario en `%LOCALAPPDATA%\Programs\Python\Python311\python.exe` (ya en el PATH de usuario; en terminales viejas el alias de la Microsoft Store puede taparlo → usar la ruta completa). Dependencias: `pip install -r requirements.txt`.
   - Git en `C:\Program Files\Git\cmd` (en el PATH de usuario). Identidad del repo: Nassim Josue Centeno Simons <nassimcenteno_2000@outlook.com>.
   - Correr el pipeline: `python tools/run_report.py` (abre el dashboard). Con `CI=true` (o `$env:CI='true'`) **no** abre el browser — usarlo al correr cosas desde el agente. `python subagents/sub_insights/analyze.py` también respeta `CI`.
3. **Commit / push — solo cuando el usuario lo pida.** Cierra los commits con la línea `Co-Authored-By: Claude …` que indique el system-reminder de la sesión. Push sin guardar credenciales: el `.env` tiene `GITHUB_PAT` (fine-grained, solo este repo, Contents + Workflows RW, gitignored):
   `git -c credential.helper= -c "http.extraheader=Authorization: Basic <base64(x-access-token:PAT)>" push origin main`
   (si falla por auth, el PAT venció: pedir uno nuevo y reemplazarlo en `.env`). Nunca imprimir el token.
4. **Publicar:** un push **no** despliega (el workflow solo corre por horario o `workflow_dispatch`). El usuario lo lanza desde Actions → *Reporte Asistencia J1* → *Run workflow*; el agente no debe dispararlo por su cuenta (el sistema lo bloquea como "production deploy"). Después, Ctrl+F5 en la página.
5. **Verificar cambios del dashboard:** Edge headless — `"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --virtual-time-budget=… --dump-dom|--screenshot file:///…`. Patrón usado: inyectar un `<script>` de prueba en una copia de `.tmp/dashboard.html` (en el scratchpad) que ejerza las 15 combinaciones de Q × 4 escenarios de proyecto/viajeros, abra los modales de todos los grupos y compare invariantes (J1+Betta = global; Con viajeros = Sin viajeros + BV por fecha; % de persona/grupo = recomputo desde historiales). Trampas: (a) Apex anima línea/marcadores/donut y la captura sale a medio dibujar → para revisar el render final usar una copia con `animations:{enabled:false}`; (b) Edge headless no baja de ~500px de viewport → para mobile meter la página en un `<iframe>` de 390px; (c) `scrollIntoView` + captura sale en blanco.
6. Antes de dar por buenos los números, correr una auditoría de consistencia (ver §8): el pipeline reconcilia entre sí, pero las diferencias suelen venir de los **datos del Sheet**.

---

## 3. Estado actual y pendientes (2026-11-06)

**Hecho y en `main`:** Q4 desde 17/10; toggle de proyecto J1/Betta; toggle Con/Sin viajeros; filtros rediseñados; selector de transiciones con las 6 combinaciones de Q; semanas parciales (≤25 participantes) en gris y fuera de las tarjetas semanales; RHO/MERCY con inicio 17/10; excepción 31/10 (GAMMA); parche de `fetch_sheets_data.py` contra `KEY_FECHA_DNI` vacía; `sub_insights` con Q4. Foto de los datos (volátil, el Sheet cambia en vivo): 304 personas, 42.6% global, 49 Fieles / 94 Activos / 134 Inconstantes / 27 Inactivos, 115 en riesgo.

**Pendiente / ideas (ninguna bloquea):**
- **Header / navegación:** se probó mover las pestañas al header + barra de filtros fija (y barra inferior en mobile) y el usuario pidió volver al layout anterior (pestañas arriba, filtros en fila propia debajo). Mejorarlo queda para más adelante.
- **Datos del Sheet por corregir (el usuario lo sabe):** 31/10 con varios GDC en 0 asistentes (probablemente sin cargar; empuja ese día a ~20% y sube "en riesgo"); GDC MERCY con 0 asistentes el 17/24/31-oct; maestro `01` con DNI repetido (Krystel Espinoza: una fila LAMBDA y otra sin grupo; DNI ficticio `12121212` compartido por 2 personas); `02` con ~17 filas duplicadas (fecha,DNI); 3 DNIs que asisten pero no están en maestro/03 (se detectaron por DNI mal digitado: Ariana Alegría se corrigió; Jhonatan Perea y Giamiria Linares quedan sin grupo); `FECHA_INGRESO` con formatos mezclados (texto, serial Excel en filas del 14 y 21/feb, un `01/07/ 2022` mal formado) y 1 persona con ingreso posterior a asistencias reales; arrastrar la fórmula de `KEY_FECHA_DNI` (col. G de `02`) para no depender del parche (~400 filas recuperadas por corrida).
- **Endurecer** la lectura de `FECHA_INGRESO` (hoy toma la primera fila de cada persona; aceptar serial Excel y espacios; usar la primera fecha válida). Hoy sin efecto (0 personas afectadas).
- **Chequeo automático** de asistencias en `02` con DNI que no existe en el maestro (hoy solo se detecta a mano).
- Bug mobile preexistente en Resumen: a ≤640px la card "Ranking de grupos" desborda ~64px (`min-width:auto` en los ítems de `.charts-2col`); el usuario prefirió dejar Resumen sin rediseño.
- El delta "vs sem. ant." del KPI de % asistencia sigue comparando contra la última semana aunque sea parcial.
- `skills/` se menciona en `CLAUDE.md` pero no existe en disco (se eliminó `skills/DESIGN_SKILL.md` en 2026-07); recrearlo solo si se necesitan estándares de UI/UX.
- `.tmp/` tiene restos viejos (capturas `n_*.png`, `live_dashboard.html`, propuestas de dashboard): desechables, ya ignorados por git.

---

## 4. Estructura del proyecto (WAT Framework)

```
config/service_account.json    ← Auth local a Google Sheets (gitignored, NUNCA subir)
.env                           ← SHEET_ID, SHEET_NAME, GITHUB_PAT (gitignored)

tools/                         ← Pipeline de producción (scripts deterministas)
  fetch_sheets_data.py         ← Google Sheets → .tmp/asistencia_raw.json (+ parche con 02)
  process_data.py              ← Reglas de negocio → .tmp/asistencia_processed.json
  generate_dashboard.py        ← ~50 líneas: inyecta el JSON en el template → .tmp/dashboard.html
  dashboard_template.html      ← TODA la UI (HTML/CSS/JS). Marcador __ASISTENCIA_DATA__ = const DATA_FULL
  run_report.py                ← Orquestador: fetch → process → generate

subagents/sub_insights/        ← Análisis profundo a demanda (no es parte del pipeline)
  analyze.py                   ← Lee asistencia_processed.json → reports/insights_report_YYYY-MM-DD.md/.html (gitignored)

workflows/                     ← SOPs
  lineamientos_reporte.md      ← REGLAS DE NEGOCIO (fuente de verdad)
  generar_reporte_asistencia.md ← Guía técnica del pipeline + features del dashboard
  analizar_insights.md         ← SOP del sub-agente

.github/workflows/reporte.yml  ← Actions: cron lunes+martes 14:00 UTC (9am Lima) + workflow_dispatch
.tmp/                          ← Intermedios (gitignored salvo .gitkeep)
```

**Pipeline:** `fetch_sheets_data.py` → `process_data.py` → `generate_dashboard.py` (en Actions además `cp .tmp/dashboard.html index.html` y deploy a Pages). **Editar el dashboard = editar `tools/dashboard_template.html`** (HTML/CSS/JS normal); el generador solo hace `template.replace("__ASISTENCIA_DATA__", json)` y valida que el marcador aparezca 1 vez.

---

## 5. Configuración crítica

- **Auth local:** `config/service_account.json` · **Auth CI:** secreto `GOOGLE_CREDENTIALS` (GitHub → Settings → Secrets → Actions).
- **Sheet ID:** `1-bEJnaHTVpQjZ2E0HQv1IZh8Hf91Jrh4nMViMS69XlE` · pestaña de reporting: `03. Asistencia_Reporting`.
- Pestañas del Sheet: `01. Imp_Maestro_J1` (roster, una fila por persona) · `02. Imp_Asistencia` (asistencias crudas: una fila por persona que asistió) · `03. Asistencia_Reporting` (log largo persona×fecha, lo que lee el pipeline) · `04. Asistencia_Visual`.
- Los logs de Actions pueden ser públicos: **no imprimir nombres ni datos personales** en `print` del pipeline (solo conteos).

---

## 6. Reglas de negocio — resumen vigente

Detalle y changelog en `workflows/lineamientos_reporte.md`. Cualquier regla nueva va **en ese archivo y en el código**.

- **Status:** Fiel >74% · Activo 41–74% · Inconstante 1–40% · Inactivo 0%. Deben coincidir `get_status()` (Python), `statusFromPct()` y `pctColor()` (template).
- **Quarters:** Q1 ene–mar · Q2 abr–jul · Q3 01/08–16/10 · **Q4 desde 17/10/2026** (`get_quarter()` + `Q4_START`). El pipeline expone `pct_q1..q4`, `asist_q*`, `total_q*`, `status_q*` por persona y `pct/asist/posibles/sesiones_q*` por grupo.
- **Excepciones de fecha vigentes (`EXCEPTIONS`):** 11/04 solo BETTA, BETTA VIAJEROS y SIGMA · 04/07 sin LAMBDA ni SIGMA · 03/10 solo BETTA VIAJEROS · 31/10 sin GDA GAMMA.
- **Grupos regidos por asistencia (`ATTENDANCE_DRIVEN_GROUPS`):** GDC BETTA y GDC BETTA VIAJEROS — fecha con 0 asistentes ⇒ no hubo sesión (dinámico y retroactivo). Si el Sheet aún no cargó la semana, esa fecha se excluye temporalmente.
- **Inicio de grupo (`GROUP_START_DATES`, solo nivel grupo):** GDC LAMBDA y GDC OMEGA 16/05/2026 · GDC RHO y GDC MERCY 17/10/2026. GDC ETA y GDA ULIMA **no** llevan entrada (decisión del usuario: gente antigua de J1).
- **Eventos (`EVENTS`, cuentan como sesión, punto naranja):** JADAK 28/02 · Montecamp 14/03 · Reencuentro Montecamp 21/03 · Apologética 02/05 · El Viaje 16/05 · Puentes 20/06 · EJEC 11/07 · Reencuentro EJEC 18/07 · J-Fest 15/08 · Alaba 05/09 · El Viaje 17/10. (El 24/10 se probó como "Reencuentro - El Viaje" y se quitó: sesión normal.)
- **Proyectos (solo presentación):** Betta = GDC BETTA, GDA GAMMA, GDC BETTA VIAJEROS, GDC OMEGA (`PROYECTO_BETTA_GROUPS`); J1 = el resto (incluye RHO y MERCY). `process_data.py` solo etiqueta `proyecto`; el dashboard recalcula en cliente (`buildView()`). Con Betta como único proyecto aparece **Con / Sin viajeros** (excluye GDC BETTA VIAJEROS de todo).
- **En Riesgo:** 0 asistencias en las últimas 4 sesiones del grupo (dinámico) · **Racha:** semanas consecutivas asistiendo (+) o ausente (−) · **Membresía formal:** `Miembro Bautizado` o `Transferido`.
- **`FECHA_INGRESO`:** las sesiones de una persona cuentan desde esa fecha (inclusive); las asistencias anteriores **no cuentan**. Una fecha mal capturada (futura, o posterior a asistencias reales) borra su historial anterior → `process_data.py` avisa el **conteo** de personas en esa situación.
- **Semanas parciales (presentación):** `total_aplica ≤ 25` (`MIN_PARTICIPANTES_SEMANA`) → punto gris y fuera de Mejor/Peor/Promedio/Semanas.
- **Filtro de entrada:** se descarta toda fila con `GRUPO_ACTUAL` vacío (esa persona no existe para el pipeline, sin importar rol/tipo). Es regla, no bug.
- **Riesgo conocido:** `GROUP_START_DATES`/`ATTENDANCE_DRIVEN_GROUPS`/`EXCEPTIONS`/`PROYECTO_BETTA_GROUPS` matchean por **nombre de grupo** (texto libre). Si el Sheet renombra un grupo, la regla se desactiva **sin error** (pasó con GDC NEW BETTA → GDC OMEGA). Revisar las claves cada vez que se reorganicen grupos.

### Arquitectura de 3 niveles (desde 2026-07)

| Nivel | Aplica `GROUP_START_DATES` | Campo en el JSON |
|---|---|---|
| **Persona** (%, historial, racha, at_risk) | NO — solo su `FECHA_INGRESO` | `sesiones`, `total_sesiones` |
| **Grupo** (tabla/modal de grupos) | SÍ | `sesiones_grupo`, `grupos[].sesiones_totales` |
| **Global** (evolución semanal) | NO — bottom-up desde personas | `evolucion` |

Por qué: el Sheet solo tiene `GRUPO_ACTUAL` (grupo de hoy), no histórico por fecha; aplicar `GROUP_START_DATES` a una persona reasignada le borraría asistencia real. **Cuidado:** el modal de grupo (`renderGroupModal`) debe usar `sesiones_grupo`, no `sesiones` (bug real: mostraba 18 sesiones en vez de 8 para GDC OMEGA). Consecuencia visible: el % por grupo del sub-agente (nivel persona) difiere un poco del de la tabla de grupos del dashboard.

---

## 7. Fuente de datos: pestañas, parche y por qué "dashboard ≠ Excel"

- El pipeline lee `03` (persona×fecha, 304 filas por fecha). `03` cruza con `02` por `KEY_FECHA_DNI` (col. G de `02`, fórmula). Si la fórmula no se arrastró a filas nuevas, la key queda vacía y `03` deja esa asistencia en **0 sin avisar**. `fetch_sheets_data.py` cruza por (fecha, DNI) con `02` y parchea (imprime cuántas). Primera detección: 16 filas el 2026-10-08; ~400 a 2026-11-06.
- **Por qué un resumen en Excel (fact) no coincide con el dashboard:** el dashboard descuenta por fecha (a) personas con `FECHA_INGRESO` posterior, (b) grupos sin sesión por excepción, (c) BETTA/BETTA VIAJEROS con 0 asistentes; no cuenta asistentes sin `GRUPO_ACTUAL` (hasta 42 en una semana), ni asistencias de DNIs ausentes del maestro, ni asistencias previas al ingreso; y deduplica filas repetidas de `02` (un conteo de filas en Excel no). `total_aplica` de la evolución ≠ "toda la gente con grupo".
- El número de personas baila entre corridas porque el Sheet cambia en vivo (histórico: 309 pipeline vs 312 maestro; hoy 304 = maestro con grupo + 1 duplicado).
- 885 asistencias están registradas en un grupo distinto al `GRUPO_ACTUAL` actual (reasignaciones): el dashboard las atribuye todas al grupo actual; la evolución de un grupo en fechas viejas refleja a sus miembros de hoy.
- Sábados sin filas (no cuentan como sesión): 28/03, 04/04, 01/08, 08/08.

---

## 8. Dashboard — estado actual (`tools/dashboard_template.html`)

Stack: Tailwind CDN + ApexCharts 3.45 + Inter + dark mode. Estado global en JS: `DATA_FULL` (JSON), `DATA` (vista activa = `buildView()`), `PSEL` (proyectos), `VSEL` (con viajeros), `QSEL` (quarters globales), `modalQ` (quarters del modal).

- **Layout:** header (marca + tema); debajo pestañas Resumen / Grupos / Personas / Riesgo; debajo, fila de filtros (Proyecto · Viajeros · Período) como controles segmentados con punto de color y contadores. Viajeros aparece con animación solo si `PSEL=={'betta'}` (pastilla deslizante `.seg-single[data-pos]`).
- **Filtros:** período global (Q1–Q4 combinables, mín. 1) → `scopedPersonas()/scopedGrupos()/scopedGlobalPct()` (con los 4 Q devuelven `DATA.*` sin tocar). No obedecen: dona por tipo, lista "En Riesgo" (solo su % por fila), matriz de status (selector propio), "Participantes"/"% membresía". Modales con su propio filtro de período (`modalQBar()`, `toggleModalQ`; `renderPersonModal()`/`renderGroupModal()`). `qChip()`/`renderQSeg()` pintan los chips (global y modales).
- **Resumen:** 7 KPI cards navegables + delta vs semana anterior · ranking de grupos · dona por tipo · evolución semanal (etiquetas en entero, decimal en tooltip; punto naranja = evento, gris = semana parcial) + 4 tarjetas (Mejor/Peor/Promedio/Semanas).
- **Grupos:** comparativa por quarter (4 series; barras horizontales en mobile) · tabla de grupos · matriz de transición de status con selector generado desde `QALL` (6 combinaciones en `<optgroup>` "Desde Qn", default = la más reciente) · modal de grupo (evolución ponderada, bottom-5).
- **Personas:** tabla con Q1%…Q4%, filtros, búsqueda, CSV · modal con racha, historial, 5 tarjetas (Q1–Q4 + selección/total; "—" si el quarter tiene 0 sesiones) y mini-chart. **Riesgo:** lista con "hace N semanas".
- **Mobile (≤640px):** cada `<tr>` lleva una celda `.mrow` (tarjeta compacta a medida; las celdas de escritorio `td[data-label]` se ocultan) en Personas/Riesgo/Grupos; el chart comparativo pasa a barras horizontales (con `horizontal:true` Apex le pega el formatter de `%` a los NOMBRES si queda en `yaxis`); la grilla de KPIs de 7 tarjetas no usa carrusel (la huérfana pasa a `grid-column:1/-1`); modal → bottom sheet.
- **Dark mode:** tokens `--accent/--pos/--warn/--neg/--q4` (+ `-soft`/`-ink`) en `:root`/`.dark`; `--accent` y `--neg` se aclaran en dark por contraste. Los charts resuelven color con `cssVar()` en cada render y `toggleDark()` re-renderiza todo (`refreshAfterThemeChange()`); `baseChartOpts()` fija `chart.background:'transparent'`.
- Nombres legacy: `renderChartQ1Q2()` / `chartQ1Q2` es la comparativa de todos los quarters (el nombre quedó de cuando eran 2).

---

## 9. Sub-agente `sub_insights` (`subagents/sub_insights/analyze.py`)

A demanda. Lee solo `asistencia_processed.json`; genera `.md` + `.html` fechados en `reports/` (gitignored) y abre el HTML (no con `CI`). Cubre Q1–Q4: semáforo con Q1–Q4% y Δ entre quarters consecutivos, momentum con una matriz por transición (`TRANSICIONES`), titulares con la transición más reciente con datos, columna vertebral con Q1–Q4%, **nuevos ingresos medidos como % desde su ingreso** (antes usaba Q2, que dejó de tener sentido con la cohorte del 17/10). Al sumar un quarter: agregarlo en `QUARTERS`/`TRANSICIONES` y en los acumuladores. Ver `workflows/analizar_insights.md`.

---

## 10. Aprendizajes técnicos

| Fecha | Aprendizaje |
|---|---|
| 2026-05 | Service Account en vez de OAuth para auth sin browser en CI; `CI=true` evita abrir browser; Pages con source "GitHub Actions" se auto-configura; pushear workflows requiere PAT con scope `workflow` |
| 2026-05 | Backslashes en regex dentro de f-strings Python rompen regex en JS → usar `data-nombre` + `this.dataset.nombre` en `onclick`. VSCode HTML preview bloquea CDN/JS → probar en Chrome/Edge |
| 2026-06 | ApexCharts no resuelve `var(--css)` dentro del canvas; puntos individuales con `markers.discrete`; el label de `annotations.yaxis` se superpone → usar HTML estático |
| 2026-07 | Separación persona/grupo/global (refactor verificado con diff exacto del JSON antes/después). Limpieza: sin imports ni detecciones de columna muertas; borrados `config/credentials.json`/`token.json` (OAuth legacy) y `skills/DESIGN_SKILL.md` |
| 2026-07 | Reorg de grupos en el Sheet: `GDA USIL [TBD]` → `GDA USIL`; `GDC EPSILON` y `GDA FAITH` disueltos; nuevos `GDC ETA`, `GDA ULIMA` (sin entrada en `GROUP_START_DATES`). 24/07: 15 inactivos de SIGMA dados de baja (`GRUPO_ACTUAL` en blanco → salen del pipeline). Fechas con asistencia casi nula en un fetch suelen ser solo datos aún no cargados |
| 2026-09 | Refactor de `generate_dashboard.py` (1255 → ~50 líneas) con la UI en `dashboard_template.html`, salida byte-idéntica. Eliminados `get_active_from()`, `group_af_map`, `"excepciones"` y `status_matrix` del JSON (muertos), `google-auth-oauthlib` de requirements |
| 2026-09 | Q3 y filtro global de período con short-circuit `if(isAllQ()) return DATA.*` (el default es idéntico al dashboard sin filtro; un drift 294→292 fue un bug de una versión intermedia). Filtro local en modales. BETTA/BETTA VIAJEROS pasan a regla de asistencia (reemplaza `GROUP_END_DATES` y 4 excepciones manuales) |
| 2026-09 | Responsive mobile rediseñado (tarjetas `.mrow`, comparativa horizontal, KPIs sin carrusel) y dark mode con tokens; `toggleDark()` re-renderiza todo |
| 2026-10 | Umbrales de status unificados (la doc decía 80/51/50, el código 74/40). `evolucion` omite fechas con `total_aplica==0` (antes emitía un 0% falso). Toggle de proyecto; el dashboard usa `DATA_FULL`/`DATA` |
| 2026-10 | Parche de `KEY_FECHA_DNI` vacía en `fetch_sheets_data.py` (ver §7). Modal de grupo: promedio de evolución ponderado (coincide con la tabla), % con 1 decimal |
| 2026-11 | Q4 desde 17/10 (`QUARTERS` de 4; en el dashboard `QALL`). Con/Sin viajeros (`VSEL`, `excludeViajeros()`). Matriz con transiciones generadas desde `QALL`. RHO y MERCY en `GROUP_START_DATES`; excepción 31/10; evento 17/10. Semanas parciales ≤25. Etiquetas del chart semanal en entero (con ~34 puntos las de 1 decimal se montaban; un halo/`dropShadow` ensucia los marcadores: no usarlo) |
| 2026-11 | Auditoría de consistencia (ver §3 y §7): pipeline y dashboard se reconcilian; las diferencias vienen de datos del Sheet. `analyze.py` pasó a Q1–Q4, respeta `CI`, perdió variables muertas (`buenos_str`, `seg_block`); `.gitignore` ignora todo `.tmp/` salvo `.gitkeep` |
| 2026-11 | Se probó un layout con pestañas en el header + barra de filtros fija + barra inferior mobile; el usuario lo descartó (§3) |
