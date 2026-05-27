# MEMORY — Reporte Asistencia J1

> Lee este archivo al inicio de cada sesión para tener contexto completo del proyecto.

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
  credentials.json             ← OAuth legacy (no se usa en producción)
  token.json                   ← OAuth token legacy

tools/                         ← Scripts Python deterministas
  fetch_sheets_data.py         ← Google Sheets → .tmp/asistencia_raw.json
  process_data.py              ← Reglas de negocio → .tmp/asistencia_processed.json
  generate_dashboard.py        ← JSON → .tmp/dashboard.html
  run_report.py                ← Orquestador: corre los 3 en secuencia
  setup_google_auth.py         ← [LEGACY] OAuth antiguo, no usar

workflows/                     ← SOPs en Markdown
  lineamientos_reporte.md      ← REGLAS DE NEGOCIO (leer antes de tocar process_data.py)
  generar_reporte_asistencia.md ← Guía técnica del pipeline + features del dashboard

.tmp/                          ← Archivos intermedios (gitignored)
  asistencia_raw.json
  asistencia_processed.json
  dashboard.html
  .gitkeep                     ← Mantiene la carpeta en git

.github/workflows/reporte.yml  ← GitHub Actions (schedule lunes+martes 14:00 UTC)
.env                           ← SHEET_ID, SHEET_NAME (gitignored)
```

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
- Eventos especiales (JADAK, Montecamp, Reencuentro)
- En Riesgo: 0 asistencias en las últimas 4 sesiones del grupo (dinámico)
- Racha actual: semanas consecutivas asistiendo (positivo) o ausente (negativo)
- Membresía formal: `Miembro Bautizado` o `Transferido`

---

## Features del dashboard (estado actual)

- KPIs globales + delta week-over-week (↑↓ vs semana anterior)
- 4 tabs: Resumen / Grupos / En Riesgo / Personas
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
