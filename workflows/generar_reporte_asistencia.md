# Workflow: Generar Reporte de Asistencia Semanal — J1

## Objetivo
Generar un dashboard HTML dinámico con la asistencia semanal del grupo J1 de la Alianza de Monterrico, leyendo los datos desde Google Sheets y abriendo el reporte en el browser.

## Inputs requeridos
- Google Sheets configurado y accesible
- `credentials.json` en la raíz del proyecto (OAuth 2.0, Desktop App)
- `token.json` generado (via `setup_google_auth.py`)
- `.env` con `SHEET_ID`, `SHEET_NAME` y `SHEET_GID`

## Herramientas
| Tool | Propósito |
|---|---|
| `tools/setup_google_auth.py` | Configuración inicial OAuth (solo una vez) |
| `tools/fetch_sheets_data.py` | Lee Google Sheets → `.tmp/asistencia_raw.json` |
| `tools/process_data.py` | Aplica reglas de negocio → `.tmp/asistencia_processed.json` |
| `tools/generate_dashboard.py` | Genera `dashboard.html` y lo abre en el browser |
| `tools/run_report.py` | **Orquestador** — ejecuta los 3 pasos en secuencia |

## Ejecución normal (uso semanal)
```bash
python tools/run_report.py
```
Eso es todo. El dashboard se abre automáticamente en el browser.

---

## Setup inicial (solo la primera vez)

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Obtener credentials.json de Google Cloud
1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo (ej: "J1-Asistencia")
3. Menú → APIs y servicios → Biblioteca → busca **Google Sheets API** → Habilitar
4. Menú → APIs y servicios → Credenciales → Crear credenciales → ID de cliente OAuth 2.0
5. Tipo de aplicación: **Aplicación de escritorio**
6. Descarga el JSON → renómbralo a `credentials.json`
7. Colócalo en la raíz del proyecto

### 3. Configurar .env
Edita el archivo `.env` en la raíz:
```
SHEET_ID=1-bEJnaHTVpQjZ2E0HQv1IZh8Hf91Jrh4nMViMS69XlE
SHEET_GID=1452026459
SHEET_NAME=<nombre exacto de la pestaña>
```

### 4. Autorizar acceso
```bash
python tools/setup_google_auth.py
```
Se abrirá el browser. Selecciona tu cuenta Google → Permitir acceso.
Confirma que aparece el mensaje `✅ Setup completo.`

---

## Reglas de negocio aplicadas

### Columnas relevantes
- **Usar `GRUPO ACTUAL`**, no `GRUPO`
- Solo se procesan personas con `GRUPO ACTUAL` no vacío (vacío = desconectado)
- `Fecha reunion STD` = fecha de la sesión
- `TIPO_MIEMBRO` vacío = no es miembro

### Excepciones de sesiones (afectan el denominador del %)
| Fecha | Regla |
|---|---|
| 11/04/2025 | Solo betta, betta viajeros y sigma tuvieron sesión |
| 02/05/2025 | Betta NO tuvo sesión |
| 23/05/2025 | Betta NO tuvo sesión |

Para el resto de grupos y fechas: todas las sesiones aplican.

### Eventos Q1 (no son sesiones regulares, pero cuentan)
| Fecha | Evento |
|---|---|
| 28/02/2025 | JADAK |
| 14/03/2025 | Montecamp |
| 21/03/2025 | Reencuentro Montecamp |

### Status por % de asistencia individual
| % | Status |
|---|---|
| 0% | Inactivo |
| 1–50% | Inconstante |
| 51–79% | Activo |
| 80%+ | Fiel |

### Períodos
- **Q1**: enero – marzo (inclusive)
- **Q2**: abril en adelante

### Tipos de grupo
- **GBU**: Grupos Universitarios
- **GDA**: Grupos de Amistad
- **GDC**: Grupos de Crecimiento

---

## Programación automática (lunes y martes)

Abrir PowerShell como administrador y ejecutar:

```powershell
# Lunes 09:00
$action = New-ScheduledTaskAction -Execute "python" -Argument "tools\run_report.py" -WorkingDirectory "C:\Users\nassim.centenosimons\OneDrive - Verisure\Documentos\CLAUDE_PROJECTS\03. JETRO_Asistencia_Semanal"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"
Register-ScheduledTask -TaskName "J1-Reporte-Lunes" -Action $action -Trigger $trigger -RunLevel Highest

# Martes 09:00
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At "09:00"
Register-ScheduledTask -TaskName "J1-Reporte-Martes" -Action $action -Trigger $trigger2 -RunLevel Highest
```

---

## Output esperado
- `dashboard.html` en la raíz del proyecto, abierto en el browser
- Secciones: KPIs globales, Asistencia por grupo, Distribución GBU/GDA/GDC, Evolución semanal, Q1 vs Q2, Tabla de participantes con filtros, Drilldown por persona

---

## Manejo de errores comunes

| Error | Causa | Solución |
|---|---|---|
| `credentials.json no encontrado` | No se descargó de Google Cloud | Seguir pasos del setup inicial |
| `token.json no encontrado` | No se corrió setup_google_auth.py | `python tools/setup_google_auth.py` |
| `Pestaña 'X' no encontrada` | SHEET_NAME incorrecto en .env | Revisar nombre exacto de la pestaña en Sheets |
| `Columnas requeridas no encontradas` | El Sheet cambió sus encabezados | Actualizar `col_map` en `process_data.py` |
| `token expired` | Token vencido | El script lo refresca automáticamente. Si falla, borrar token.json y re-correr setup |

---

## Aprendizajes y actualizaciones

*(Documenta aquí cualquier cambio en el Sheets, nuevas excepciones de fechas o ajustes al cálculo)*

- **2025-05-26**: Setup inicial del proyecto. Excepciones de fechas codificadas en `process_data.py > EXCEPTIONS`.
