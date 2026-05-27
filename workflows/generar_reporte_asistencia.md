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
| `generate_dashboard.py` | `asistencia_processed.json` | `.tmp/dashboard.html` | Genera el HTML interactivo |
| `run_report.py` | — | Corre los 3 anteriores | Orquestador para uso local |
| `setup_google_auth.py` | — | `config/token.json` | **[LEGACY]** OAuth antiguo, no usar |

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
- Excepciones de fechas por grupo
- Eventos especiales
- Definición de "En Riesgo" y racha actual
- Membresía formal

Al agregar una nueva excepción o lineamiento: actualizar ese archivo **y** el código en `process_data.py`.

---

## Features del dashboard

El dashboard generado incluye:

**Análisis:**
- KPIs globales con delta week-over-week (↑↓ vs semana anterior)
- Distribución de status por tipo de grupo (GBU / GDA / GDC)
- Evolución semanal de asistencia con eventos especiales destacados
- Comparativa Q1 vs Q2 por grupo
- Matriz de transición de status Q1 → Q2

**Navegación:**
- 4 tabs: Resumen / Grupos / En Riesgo / Personas
- KPI cards clickeables → navegan a la vista filtrada
- Modal de detalle por persona: racha actual 🔥/❄️, historial visual, mini-chart
- Modal de detalle por grupo: evolución propia + ranking de menor asistencia

**Tablas:**
- Ordenamiento por cualquier columna (click en encabezado)
- Filtros por tipo, grupo, status
- Búsqueda por nombre
- Exportar CSV (datos actualmente filtrados)
- "Hace N semanas" en lista de riesgo (en vez de fecha cruda)

**Mobile:**
- Tablas se convierten en cards apiladas en pantallas < 640px
- Modal como bottom sheet en mobile
- Tabs con iconos, header compacto
- Charts con soporte táctil (touch events)

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
