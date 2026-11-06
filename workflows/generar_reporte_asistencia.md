# Workflow: Generar Reporte de Asistencia Semanal — J1

## Objetivo
Generar un dashboard HTML interactivo con la asistencia semanal del grupo J1 de la Alianza de Monterrico, publicado automáticamente en GitHub Pages.

**URL pública:** https://nassimcenteno.github.io/asistencia_j1/

---

## Inputs requeridos

| Input | Local | GitHub Actions |
|---|---|---|
| Credenciales Google | `config/service_account.json` | Secreto `GOOGLE_CREDENTIALS` |
| Sheet ID | `.env` → `SHEET_ID` | Hardcoded en `reporte.yml` |
| Sheet Name | `.env` → `SHEET_NAME` | Hardcoded en `reporte.yml` |

---

## Pipeline de herramientas

| Script | Input | Output | Descripción |
|---|---|---|---|
| `fetch_sheets_data.py` | Google Sheets | `.tmp/asistencia_raw.json` | Descarga datos crudos vía Service Account |
| `process_data.py` | `asistencia_raw.json` | `.tmp/asistencia_processed.json` | Aplica todas las reglas de negocio |
| `generate_dashboard.py` | `asistencia_processed.json` + `tools/dashboard_template.html` | `.tmp/dashboard.html` | Inyecta el JSON en el template (`__ASISTENCIA_DATA__` → `const DATA`). ~40 líneas |
| `run_report.py` | — | Corre los 3 anteriores | Orquestador para uso local |

**Notas de los scripts:**
- `fetch_sheets_data.py` cruza `02. Imp_Asistencia` por (fecha, DNI) y parchea las asistencias que `03` dejó en 0 por `KEY_FECHA_DNI` vacía (imprime cuántas; si aparece seguido, arrastrar la fórmula de la columna G en `02`).
- `process_data.py` imprime el **conteo** de personas con asistencias previas a su `FECHA_INGRESO` (sin nombres: los logs de Actions pueden ser públicos).

**La UI del dashboard vive en `tools/dashboard_template.html`** — HTML/CSS/JS normal. Para cambiar el dashboard se edita ese archivo directamente (no hay f-string con llaves duplicadas). `generate_dashboard.py` no contiene markup.

---

## Ejecución local

```bash
python tools/run_report.py
```

El dashboard se abre automáticamente en el browser desde `.tmp/dashboard.html`.

---

## Ejecución automática

GitHub Actions corre el pipeline los **lunes y martes a las 9am Lima** (14:00 UTC).
También puede ejecutarse manualmente desde la pestaña **Actions** del repo.

---

## Reglas de negocio

**Ver `workflows/lineamientos_reporte.md`** — es la única fuente de verdad para:
- Thresholds de status (Fiel / Activo / Inconstante / Inactivo)
- Excepciones de fechas por grupo, eventos especiales, grupos regidos por asistencia (BETTA / BETTA VIAJEROS)
- Los 3 niveles de cálculo: persona / grupo / global (sección 10 del documento)
- Definición de "En Riesgo" y racha actual
- Membresía formal

Al agregar una nueva excepción o lineamiento: actualizar ese archivo **y** el código en `process_data.py`.

**Importante:** las claves de `GROUP_START_DATES` y `ATTENDANCE_DRIVEN_GROUPS` deben coincidir exactamente con `GRUPO_ACTUAL` en el Sheet. Si un grupo se renombra ahí, hay que actualizar la clave en `process_data.py` o la regla deja de aplicarse **sin error** (ya pasó una vez con GDC NEW BETTA → GDC OMEGA).

---

## Features del dashboard

Stack: **Tailwind CSS CDN + ApexCharts + Inter font + dark mode** (CSS custom properties). Estado en JS: `DATA_FULL` (JSON), `DATA` (vista activa tras filtro de proyecto/viajeros), `PSEL`, `VSEL`, `QSEL`, `modalQ`.

**Fila de filtros** (debajo de las pestañas; controles segmentados con punto de color y contadores):
- **Proyecto (J1 / Betta):** chips combinables (mín. 1) con contador de personas. Betta = BETTA, GAMMA, BETTA VIAJEROS, OMEGA; J1 = el resto. Con ambos activos no cambia nada; con uno solo se recalculan KPIs, dona, evolución, riesgo, rankings y tablas (`buildView()`) y se resetean los selects de grupo. Ver `lineamientos_reporte.md` §14.
- **Viajeros (Con / Sin):** aparece solo cuando Betta es el único proyecto; "Sin viajeros" excluye a GDC BETTA VIAJEROS de todo el dashboard (KPIs, tablas, gráficos, riesgo, modales, CSV).
- **Período:** chips Q1/Q2/Q3/Q4 combinables (mín. 1; Q4 = desde el 17/10/2026). Recalcula KPIs, ranking, evolución, tablas de grupos y personas y el CSV. Con los 4 Q activos no recalcula nada (idéntico a sin filtro). No afecta: dona por tipo (poblacional), lista de "En Riesgo" (global; solo su % por fila obedece), matriz de status (selector propio), "Participantes"/"% membresía" (roster completo).
- **En los pop-ups** (persona y grupo) hay una fila de chips Q propia, independiente del global (arranca copiándolo).

**4 tabs:** Resumen / Grupos / Personas / Riesgo

**Tab Resumen:**
- 7 KPI cards navegables (filtran la tabla correspondiente) con delta vs semana anterior
- Ranking de grupos por % asistencia con línea de referencia al promedio
- Donut por tipo de grupo (GBU / GDA / GDC) con overlay HTML para el total
- Evolución semanal: área con gradiente, etiquetas de % en entero (el decimal va en el tooltip), punto naranja = evento, **punto gris = semana parcial** (≤25 participantes), línea punteada de promedio
- 4 tarjetas: Mejor semana / Peor semana / Promedio semanal / Semanas — **excluyen las semanas parciales** (la de Semanas indica cuántas; ver `lineamientos_reporte.md` §15)

**Tab Grupos:**
- Comparativa por quarter por grupo (Q1–Q4, columnas; barras horizontales en mobile)
- Tabla de grupos: personas, sesiones (según `GROUP_START_DATES`), % asistencia, % membresía, distribución de status
- Matriz de transición de status con selector de las **6 combinaciones** de quarters (`<optgroup>` "Desde Qn"; default = la más reciente), calculada en cliente desde `status_q*`
- Modal de grupo: evolución (usa `sesiones_grupo`; promedio ponderado = % de la tabla) + ranking de menor asistencia

**Tab Personas:** tabla filtrable/ordenable con Q1%…Q4% y export CSV · modal con racha, historial por sesión, 5 tarjetas (Q1–Q4 + selección/total; "—" si el quarter no tiene sesiones) y mini-chart.

**Tab Riesgo:** lista de personas en riesgo con "hace N semanas" (no fecha cruda).

**Mobile (≤640px):** tarjetas compactas `.mrow` en Personas/Riesgo/Grupos, modal como bottom sheet, filtros apilados a todo el ancho.

---

## Setup inicial (solo la primera vez)

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar `.env`
```
SHEET_ID=1-bEJnaHTVpQjZ2E0HQv1IZh8Hf91Jrh4nMViMS69XlE
SHEET_NAME=03. Asistencia_Reporting
```

### 3. Colocar `service_account.json`
Descargar desde Google Cloud Console → IAM → Cuentas de servicio → Crear clave → JSON.
Colocar en `config/service_account.json`. **Nunca subir al repo** (está en `.gitignore`).

### 4. Compartir el Sheet con la Service Account
En Google Sheets → Compartir → pegar el `client_email` del JSON → acceso Lector.

---

## Estructura de archivos generados

```
.tmp/
  asistencia_raw.json        ← datos crudos del Sheet (gitignored)
  asistencia_processed.json  ← datos procesados con reglas de negocio (gitignored)
  dashboard.html             ← dashboard generado (gitignored)
  .gitkeep                   ← garantiza que la carpeta exista en el repo
```

GitHub Actions copia `.tmp/dashboard.html` → `index.html` antes de publicar en Pages.

---

## Manejo de errores comunes

| Error | Causa | Solución |
|---|---|---|
| `No se encontro service_account.json` | Falta el archivo en `config/` | Colocar el JSON en `config/service_account.json` |
| `Pestaña 'X' no encontrada` | `SHEET_NAME` incorrecto | Revisar nombre exacto de la pestaña en Sheets |
| `Columnas requeridas no encontradas` | El Sheet cambió sus encabezados | Actualizar `col_map` en `process_data.py` |
| GitHub Actions falla en fetch | Secreto `GOOGLE_CREDENTIALS` mal configurado | Verificar en Settings → Secrets → Actions |
| Dashboard en blanco en browser | Error JS (ver DevTools → Console) | Verificar que el JSON procesado es válido |

---

## Aprendizajes técnicos

| Fecha | Aprendizaje |
|---|---|
| 2026-05 | Migración de OAuth a Service Account — permite auth sin browser en CI |
| 2026-05 | `CI=true` en GitHub Actions → guard `if not os.getenv("CI")` evita abrir browser |
| 2026-05 | GitHub Pages con source "GitHub Actions" se auto-configura, no requiere botón Save |
| 2026-05 | Push de workflow files requiere PAT con scope `workflow` (además de `repo`) |
| 2026-05 | En f-strings de Python, backslashes en regex JS generan regex rotas — usar `data-nombre` + `this.dataset.nombre` para onclick seguros con nombres que tengan apóstrofes |
| 2026-05 | VSCode HTML preview no ejecuta JS externo (CDN) — siempre probar en Chrome/Edge |
| 2026-06 | ApexCharts no resuelve `var(--css)` dentro del canvas — usar hex hardcodeado o overlay HTML |
| 2026-06 | Para colorear puntos individuales en ApexCharts usar `markers.discrete` (NO `markers.colors` array) |
| 2026-06 | Label de `annotations.yaxis` siempre se superpone al chart — moverlo a HTML estático fuera del chart |
| 2026-07 | Cada persona trae dos historiales en el JSON: `sesiones` (nivel persona, sin `GROUP_START_DATES`) y `sesiones_grupo` (nivel grupo, con `GROUP_START_DATES`). El modal de grupo debe usar `sesiones_grupo` — usar `sesiones` ahí infla el conteo de sesiones del grupo con historial que no le corresponde |
| 2026-09 | 3 quarters (Q1/Q2/Q3). Lógica per-quarter generalizada a dicts keyed por `QUARTERS` en `process_data.py` (no copiar `q1`/`q2`/`q3` a mano). La matriz de status del dashboard se recalcula client-side (`MATRIX_TRANS` + selector); el `status_matrix` del JSON era muerto y se eliminó. Para agregar Q4 / cerrar Q3: tocar `get_quarter()` + tabla en `lineamientos_reporte.md`, el resto se propaga solo |
| 2026-07 | `GROUP_START_DATES`/`ATTENDANCE_DRIVEN_GROUPS` matchean por nombre de grupo como texto libre — un rename en el Sheet (ej. GDC NEW BETTA → GDC OMEGA) desactiva la regla sin error. Validar la clave cada vez que el Sheet reorganice grupos |
| 2026-09 | BETTA / BETTA VIAJEROS: se reemplazó el hold `GROUP_END_DATES` y sus excepciones manuales por la regla de asistencia (`ATTENDANCE_DRIVEN_GROUPS` + `group_had_session()`): 0 asistentes en una fecha ⇒ no hubo sesión, retroactivo. El dashboard no requirió cambios — solo presenta `sesiones_totales`/`sesiones_qN`/`pct_*` que ya salen ajustados de `process_data.py` |
| 2026-11 | 4 quarters (Q4 desde 17/10/2026): al sumar uno nuevo tocar `get_quarter()`/`Q4_START` + `QUARTERS` en `process_data.py`, `QALL`/`Q_INFO`/`Q_META_BASE` y la tabla Personas en el template, `QUARTERS`/`TRANSICIONES` en `analyze.py` y la tabla de `lineamientos_reporte.md` §2 (la matriz de transiciones y los chips se generan solos). Con un solo proyecto filtrado hay más semanas ≤25 participantes. Verificar charts en Edge headless con animaciones desactivadas |
