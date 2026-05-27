# Workflow: Generar Reporte de Asistencia Semanal — J1

## Objetivo
Generar un dashboard HTML dinámico con la asistencia semanal del grupo J1 de la Alianza de Monterrico, publicado automáticamente en GitHub Pages.

## Inputs requeridos
- Google Sheet accesible por la Service Account
- `config/service_account.json` (local) o secreto `GOOGLE_CREDENTIALS` (GitHub Actions)
- `.env` con `SHEET_ID` y `SHEET_NAME`

## Herramientas
| Tool | Propósito |
|---|---|
| `tools/fetch_sheets_data.py` | Lee Google Sheets → `.tmp/asistencia_raw.json` |
| `tools/process_data.py` | Aplica reglas de negocio → `.tmp/asistencia_processed.json` |
| `tools/generate_dashboard.py` | Genera `.tmp/dashboard.html` y lo abre en el browser |
| `tools/run_report.py` | **Orquestador** — ejecuta los 3 pasos en secuencia |
| `tools/setup_google_auth.py` | Setup OAuth legacy (no necesario para CI) |

## Ejecución normal (uso local)
```bash
python tools/run_report.py
```
El dashboard se abre automáticamente en el browser desde `.tmp/dashboard.html`.

## Ejecución automática (lunes y martes 9am Lima)
GitHub Actions corre el pipeline en la nube sin intervención manual.
Publicado en: **https://nassimcenteno.github.io/asistencia_j1/**

---

## Reglas de negocio
**Ver `workflows/lineamientos_reporte.md`** — ahí están TODAS las reglas de negocio codificadas.
Al agregar una nueva excepción o lineamiento: actualizar ese archivo Y el código en `process_data.py`.

---

## Setup inicial (solo la primera vez)

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar .env
```
SHEET_ID=1-bEJnaHTVpQjZ2E0HQv1IZh8Hf91Jrh4nMViMS69XlE
SHEET_NAME=03. Asistencia_Reporting
```

### 3. Colocar service_account.json
Descargar desde Google Cloud Console y colocar en `config/service_account.json`.
**Nunca subir al repo** (está en `.gitignore`).

---

## Estructura de archivos generados

```
.tmp/
  asistencia_raw.json        ← datos crudos del Sheet
  asistencia_processed.json  ← datos procesados con reglas de negocio
  dashboard.html             ← dashboard generado (entregable intermedio)
```

GitHub Actions copia `.tmp/dashboard.html` → `index.html` antes de publicar.

---

## Manejo de errores comunes

| Error | Causa | Solución |
|---|---|---|
| `No se encontro service_account.json` | Falta el archivo en `config/` | Colocar el JSON en `config/service_account.json` |
| `Pestaña 'X' no encontrada` | SHEET_NAME incorrecto en .env | Revisar nombre exacto de la pestaña en Sheets |
| `Columnas requeridas no encontradas` | El Sheet cambió sus encabezados | Actualizar `col_map` en `process_data.py` |
| GitHub Actions falla en fetch | Secreto `GOOGLE_CREDENTIALS` mal configurado | Verificar el secreto en Settings → Secrets → Actions |

---

## Aprendizajes

- **2026-05**: Migración de OAuth a Service Account para permitir auth sin browser en CI.
- **2026-05**: Guard `if not os.getenv("CI")` en `generate_dashboard.py` evita error de display en GitHub Actions.
- **2026-05**: GitHub Pages con source "GitHub Actions" no requiere botón Save — se configura automáticamente.
