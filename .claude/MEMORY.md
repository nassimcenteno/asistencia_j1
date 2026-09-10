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
  generate_dashboard.py        ← JSON → .tmp/dashboard.html
  run_report.py                ← Orquestador: corre los 3 en secuencia

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

**Nota:** `skills/DESIGN_SKILL.md` fue eliminado (2026-07) — la carpeta `skills/` sigue existiendo en `CLAUDE.md` como concepto pero hoy está vacía. Si se necesitan estándares de UI/UX para el dashboard, evaluar recrearla.

---

## Inventario de scripts

| Script | Input | Output | Uso |
|---|---|---|---|
| `fetch_sheets_data.py` | Google Sheets (SA o env var) | `asistencia_raw.json` | Paso 1 |
| `process_data.py` | `asistencia_raw.json` | `asistencia_processed.json` | Paso 2 |
| `generate_dashboard.py` | `asistencia_processed.json` | `dashboard.html` | Paso 3 |
| `run_report.py` | — | Corre los 3 en secuencia | Uso local |

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
- Excepciones de fechas por grupo (denominador del %)
- Eventos especiales (JADAK, Montecamp, Reencuentro, Apologética, El Viaje, Puentes)
- Grupos en hold (`GROUP_END_DATES`): dejan de contar sesiones desde una fecha (ej. GDC BETTA VIAJEROS desde 27/6)
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

**Cuidado al tocar el dashboard:** el modal de grupo (`openGroupDrilldown` en `generate_dashboard.py`) debe usar `sesiones_grupo`, no `sesiones` — usar el campo equivocado ahí fue un bug real (mostraba 18 sesiones en vez de 8 para GDC OMEGA).

**Riesgo conocido:** `GROUP_START_DATES`/`GROUP_END_DATES`/`EXCEPTIONS` matchean por nombre de grupo (texto libre, sin ID estable). Si el Sheet renombra un grupo, la regla se desactiva **sin error** — pasó con GDC NEW BETTA → GDC OMEGA (2026-07).

### Filtro de entrada: `GRUPO_ACTUAL` en blanco

`process_data.py` descarta **toda fila** cuya columna `GRUPO_ACTUAL` venga vacía (`if not grupo_actual: continue`, ~línea 187). Consecuencia: una persona sin grupo asignado **no existe** para el pipeline — no aparece en KPIs, tablas, dashboard ni sub-agente, sin importar su `ROL_ACTUAL` ni `TIPO_MIEMBRO`. Los **mentores activos sin grupo** (gente entre asignaciones) quedan fuera por esto — no es un bug ni una regresión, siempre fue así. Si se quiere mostrarlos hay que cambiar la regla explícitamente (ej. bucket "sin grupo" que no afecte métricas por grupo, decidir si cuentan en KPIs globales).

### Denominador semanal (`total_aplica` en `evolucion`)

No es "toda la gente con `GRUPO_ACTUAL`". Por cada fecha excluye además: (1) grupos en hold (`GROUP_END_DATES`) desde su fecha de hold, y (2) personas con `FECHA_INGRESO` posterior a esa fecha. Por eso el denominador de una semana puede ser menor que el total de personas activas.

### Fuente: pestaña vs. "maestro"

El pipeline lee la pestaña `03. Asistencia_Reporting` (log largo, una fila por persona×fecha). El usuario tiene además un "maestro" (roster, una fila por persona). Los conteos pueden no cuadrar (ej. 309 en el pipeline vs 312 en el maestro) si la pestaña de reporting va atrasada respecto al maestro.

---

## Features del dashboard (estado actual)

- KPIs globales + delta week-over-week (↑↓ vs semana anterior)
- 4 tabs: Resumen / Grupos / Personas / Riesgo
- Gráficos: barras por grupo, dona por tipo, evolución semanal, Q1 vs Q2
- Tablas ordenables por cualquier columna + filtros + búsqueda + exportar CSV
- Modal persona: racha 🔥/❄️, historial visual por sesión, mini-chart Q1/Q2/Total
- Modal grupo: evolución del grupo + ranking de menor asistencia (clickeable)
- "Hace N semanas" en lista de riesgo
- KPI cards navegables → filtran la tabla correspondiente
- Matriz de transición de status Q1 → Q2
- **Responsive mobile:** tablas → cards, modal → bottom sheet, tabs con iconos

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
| 2026-07-24 | Limpieza en el Sheet: 15 miembros inactivos de `GDC SIGMA` (0% asistencia todo el ciclo, racha -20) dados de baja del grupo — `GRUPO_ACTUAL` y `ROL_ACTUAL` puestos en blanco → salen del pipeline. Además 4 mentores que ya estaban sin grupo (incluido el owner) perdieron su `ROL_ACTUAL` de "Mentor". Ninguno de esos 4 aparecía en el dashboard antes tampoco (ver "Filtro de entrada: `GRUPO_ACTUAL` en blanco"). El conteo total de personas bajó a 309; el maestro del usuario marca 312 (posible desfase entre pestañas) |
