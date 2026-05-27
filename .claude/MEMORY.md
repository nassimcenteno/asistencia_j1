# MEMORY — Reporte Asistencia J1

> Lee este archivo al inicio de cada sesión para tener contexto completo del proyecto.

## Contexto
Automatización del control de asistencia semanal del grupo J1 (jóvenes) de la Alianza de Monterrico, Lima, Perú.
El dashboard se genera automáticamente los **lunes y martes 9am Lima** via GitHub Actions y se publica en:
**https://nassimcenteno.github.io/asistencia_j1/**

---

## Estructura del proyecto (WAT Framework)

```
config/             ← Credenciales (gitignored). NUNCA subir al repo.
  service_account.json   ← Auth local para Google Sheets (sin browser)
  credentials.json       ← OAuth legacy (no se usa en producción)
  token.json             ← OAuth token legacy

tools/              ← Scripts Python deterministas
  fetch_sheets_data.py   ← Lee Google Sheets → .tmp/asistencia_raw.json
  process_data.py        ← Aplica reglas de negocio → .tmp/asistencia_processed.json
  generate_dashboard.py  ← Genera .tmp/dashboard.html
  run_report.py          ← Orquestador: corre los 3 scripts en secuencia
  setup_google_auth.py   ← Setup OAuth legacy (ya no necesario para CI)

workflows/          ← SOPs en Markdown
  generar_reporte_asistencia.md  ← Guía técnica del pipeline
  lineamientos_reporte.md        ← LINEAMIENTOS DE NEGOCIO (leer siempre antes de tocar process_data.py)

.tmp/               ← Archivos intermedios generados (gitignored)
  asistencia_raw.json
  asistencia_processed.json
  dashboard.html

.github/workflows/reporte.yml  ← GitHub Actions (schedule lunes+martes)
.env                           ← SHEET_ID, SHEET_NAME, GITHUB_TOKEN (gitignored)
```

---

## Inventario de Skills (Tools)

| Script | Input | Output | Cuándo usarlo |
|---|---|---|---|
| `fetch_sheets_data.py` | Google Sheets (via SA o env var) | `.tmp/asistencia_raw.json` | Siempre primero |
| `process_data.py` | `.tmp/asistencia_raw.json` | `.tmp/asistencia_processed.json` | Después de fetch |
| `generate_dashboard.py` | `.tmp/asistencia_processed.json` | `.tmp/dashboard.html` | Después de process |
| `run_report.py` | — | Corre los 3 anteriores en secuencia | Ejecución local completa |
| `setup_google_auth.py` | — | `config/token.json` | Solo si necesitas OAuth (legacy) |

**Ejecución local:** `python tools/run_report.py`
**En GitHub Actions:** los 3 scripts corren individualmente en secuencia.

---

## Configuración crítica

- **Auth local**: `config/service_account.json` (gitignored, nunca subir)
- **Auth CI**: secreto `GOOGLE_CREDENTIALS` en GitHub → Settings → Secrets → Actions
- **Sheet**: ID `1-bEJnaHTVpQjZ2E0HQv1IZh8Hf91Jrh4nMViMS69XlE`, pestaña `03. Asistencia_Reporting`
- **Repo GitHub**: https://github.com/nassimcenteno/asistencia_j1

---

## Lineamientos de negocio
Ver **`workflows/lineamientos_reporte.md`** — ahí están TODAS las reglas que el usuario ha definido.
Son la única fuente de verdad para excepciones de fechas, definición de status, eventos, etc.

---

## Aprendizajes técnicos

| Fecha | Aprendizaje |
|---|---|
| 2026-05 | GitHub Actions no tiene browser → usar Service Account en vez de OAuth |
| 2026-05 | `CI=true` env var existe en GitHub Actions → guard en generate_dashboard.py para no abrir browser |
| 2026-05 | Push de workflow files requiere PAT con scope `workflow` (además de `repo`) |
| 2026-05 | GitHub Pages con source "GitHub Actions" no necesita botón Save — se auto-configura |
| 2026-05 | `asistencia_j1` es el nombre del repo (con underscore, no hyphen) |
