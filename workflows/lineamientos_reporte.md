# Lineamientos del Reporte de Asistencia — J1

> **FUENTE DE VERDAD para todas las reglas de negocio.**
> Antes de modificar `process_data.py` o `generate_dashboard.py`, leer este archivo.
> Cuando el usuario da un nuevo lineamiento permanente, agregarlo aquí Y al código.

---

## 1. Definición de Status (% asistencia individual)

| % Asistencia | Status |
|---|---|
| 0% | Inactivo |
| 1% – 50% | Inconstante |
| 51% – 79% | Activo |
| 80%+ | Fiel |

Se calcula sobre el total de sesiones que **aplican al grupo** (ver sección 4).

---

## 2. Períodos

| Período | Meses |
|---|---|
| **Q1** | Enero – Marzo (inclusive) |
| **Q2** | Abril en adelante |

---

## 3. Tipos de grupo

| Código | Nombre completo |
|---|---|
| GBU | Grupos Universitarios |
| GDA | Grupos de Amistad |
| GDC | Grupos de Crecimiento |

---

## 4. Excepciones de fechas (afectan el denominador del %)

Estas fechas NO son sesiones universales — solo aplican a ciertos grupos.
Al agregar una nueva excepción: actualizar aquí Y en `EXCEPTIONS` en `process_data.py`.

| Fecha | Regla |
|---|---|
| **11/04/2026** | SOLO tuvieron sesión: GDC BETTA, GDC BETTA VIAJEROS, GDC SIGMA. El resto NO cuenta esta fecha. |
| **02/05/2026** | GDC BETTA **no** tuvo sesión — excluir de su denominador. |
| **23/05/2026** | GDC BETTA **no** tuvo sesión — excluir de su denominador. |
| **30/05/2026** | GDC BETTA VIAJEROS **no** tuvo sesión — excluir de su denominador. |
| **06/06/2026** | GDC BETTA **no** tuvo sesión — excluir de su denominador. |
| **04/07/2026** | GDC LAMBDA y GDC SIGMA **no** tuvieron sesión (por acuerdo) — excluir de su denominador. |

**Regla por defecto:** Si una fecha no está en excepciones, aplica a TODOS los grupos.

---

## 5. Eventos especiales (cuentan como sesión)

No son sesiones regulares pero sí cuentan en el % de asistencia.
Aparecen como punto naranja en el gráfico de evolución del dashboard.

| Fecha | Evento |
|---|---|
| **28/02/2026** | JADAK |
| **14/03/2026** | Montecamp |
| **21/03/2026** | Reencuentro Montecamp |
| **02/05/2026** | Apologética |
| **16/05/2026** | El Viaje |
| **20/06/2026** | Puentes |
| **11/07/2026** | EJEC |
| **18/07/2026** | Reencuentro EJEC |

---

## 6. Definición de "En Riesgo"

Una persona está **en riesgo** si tiene **0 asistencias en las últimas 4 sesiones** que aplican a su grupo.

El cálculo es **dinámico**: toma automáticamente las 4 fechas más recientes del historial de cada grupo. No requiere actualización manual al agregar nuevas sesiones.

---

## 7. Racha actual (campo computado)

Cada persona tiene un campo `racha_actual` calculado en `process_data.py`:

- **Valor positivo** = N semanas asistiendo consecutivamente (desde la sesión más reciente)
- **Valor negativo** = N semanas ausentes consecutivamente
- **0** = sin historial

Ejemplos: `3` → asistió las últimas 3 sesiones. `-4` → ausente las últimas 4 sesiones.
Se muestra en el modal de detalle de cada persona en el dashboard.

---

## 8. Reglas de inclusión de personas

- Solo se incluyen personas con **GRUPO ACTUAL** no vacío.
- Vacío en GRUPO ACTUAL = persona desconectada = no aparece en el reporte.
- Se usa la columna `GRUPO ACTUAL`, NO la columna `GRUPO`.

---

## 9. Membresía formal

Los tipos de miembro que se consideran **miembros formales**:
- `Miembro Bautizado`
- `Transferido`

Cualquier otro valor (o vacío) = no es miembro formal.

---

## 10. Separación de conceptos: persona vs. grupo vs. global

**Regla de arquitectura (desde 2026-07):** el pipeline calcula tres cosas de forma independiente, cada una con sus propias reglas:

1. **Nivel persona** (`total_sesiones`, `pct_total`, `historial`, `at_risk`, `racha_actual`, status): se basa **únicamente** en su propia `FECHA_INGRESO` (si la tiene) + `EXCEPTIONS` + hold del grupo (`GROUP_END_DATES`). **No aplica `GROUP_START_DATES`.** Refleja la trayectoria real de la persona, sin importar cómo se llama o cuándo se creó su grupo actual.
2. **Nivel grupo** (tabla de grupos: `sesiones_totales`, `pct_asistencia`, `pct_q1`, `pct_q2`): sí aplica `GROUP_START_DATES` (además de `EXCEPTIONS` y hold). Se calcula de forma independiente — **ya no es la suma de los totales de cada persona** — usando el flag interno `aplica_grupo` por sesión, que combina la fecha de inicio del grupo con la `FECHA_INGRESO` de cada miembro (lo que sea más tardío).
3. **Nivel global** (evolución semanal, % general): se calcula bottom-up desde las personas (nivel 1), por lo tanto tampoco aplica `GROUP_START_DATES`.

**Por qué:** el Sheet solo tiene la columna `GRUPO_ACTUAL` (el grupo de hoy), no un histórico de grupo por fecha. Si una persona lleva tiempo en J1 pero fue reasignada a un grupo recién creado o renombrado, aplicarle la fecha de inicio del grupo le borraría asistencia real de su historial. Separar los tres niveles evita ese problema sin perder la utilidad de `GROUP_START_DATES` para medir el desempeño del grupo desde que existe. Cuando se agregue una columna de grupo histórico por fecha, se podrá revisar esta lógica.

## 11. Fecha de inicio de grupos (GROUP_START_DATES) — solo nivel grupo

Algunos grupos fueron creados durante el ciclo y no existían desde el inicio. Estos grupos tienen una fecha de inicio codificada en `GROUP_START_DATES` en `process_data.py`. Esto solo afecta las métricas **de grupo** (sección 10, nivel 2): la columna **Sesiones** y el % de asistencia en la tabla de grupos reflejan solo las sesiones desde ese punto (inclusive). No afecta el % ni el historial individual de sus miembros.

| Grupo | Fecha de creación | Active from |
|---|---|---|
| GDC LAMBDA | 16/05/2026 | 16/05/2026 |
| GDC OMEGA (antes "GDC NEW BETTA") | 16/05/2026 | 16/05/2026 |

**Importante:** la clave en `GROUP_START_DATES` debe coincidir con el `GRUPO_ACTUAL` vigente en el Sheet. Si un grupo cambia de nombre (como pasó con NEW BETTA → OMEGA), hay que actualizar la clave aquí Y en el código, o la regla deja de aplicarse silenciosamente (sin error).

Aplicación en el código:
- `group_af_map` se computa antes del loop de filas
- `aplica_grupo` (por sesión) combina `group_af_map` con la `FECHA_INGRESO` de cada persona → usado para agregar las métricas de grupo
- `sesiones_por_grupo` (con `GROUP_START_DATES`) → `sesiones_totales` en la tabla de grupos
- `sesiones_por_grupo_persona` (sin `GROUP_START_DATES`) → historial y denominador de cada persona

Al agregar un nuevo grupo con fecha de inicio, o renombrar uno existente: actualizar `GROUP_START_DATES` en `process_data.py` Y esta tabla.

---

## 12. Grupos en hold (GROUP_END_DATES)

Algunos grupos quedan en pausa ("hold") durante el ciclo: dejan de tener sesiones pero sus miembros siguen apareciendo en el reporte. Las sesiones desde la fecha de hold (inclusive) ya NO cuentan ni en el denominador ni en el numerador de sus miembros, ni en el `total_aplica` de la evolución semanal.

| Grupo | Hold desde (inclusive) |
|---|---|
| GDC BETTA VIAJEROS | 27/06/2026 |

Aplicación en el código: `session_before_group_end()` en `process_data.py`, usada en el cálculo de `aplica_denominador` por sesión, en `sesiones_por_grupo` y en `total_aplica` de la evolución semanal.

Al poner un grupo en hold: actualizar `GROUP_END_DATES` en `process_data.py` Y esta tabla.

---

## 13. Fecha de ingreso individual (FECHA_INGRESO)

Si una persona tiene la columna `FECHA_INGRESO` con un valor, sus sesiones **solo cuentan desde esa fecha en adelante (inclusive)**.

- Sesiones previas a esa fecha: no afectan su numerador, ni su denominador, ni el `total_aplica` de la evolución semanal del grupo.
- Si la fecha de ingreso no coincide con una fecha de sesión, la primera sesión aplicable es la primera fecha de sesión >= `FECHA_INGRESO`.

**Ejemplo:** Ingreso el 16/05/2026 (sábado) → `active_from` = 16/05/2026. Cuenta sesiones desde el 16/5 en adelante.
**Ejemplo:** Ingreso el 17/05/2026 (domingo) → `active_from` = 17/05/2026. Primera sesión aplicable: 23/05/2026.

Al agregar personas nuevas con FECHA_INGRESO: no requiere cambio de código. El pipeline lo detecta automáticamente desde la columna del Sheet.

---

## Historial de cambios

| Fecha | Cambio |
|---|---|
| 2026-05 | Setup inicial del proyecto |
| 2026-05 | Excepciones 11/4, 2/5, 23/5 codificadas |
| 2026-05 | Eventos JADAK, Montecamp, Reencuentro registrados |
| 2026-05 | `racha_actual` agregado como campo computado por persona |
| 2026-05 | Dashboard: responsive mobile, ordenamiento de tablas, exportar CSV, delta WoW, KPI cards navegables, modal de grupo |
| 2026-06 | Evento APOLOGÉTICA (02/05) registrado |
| 2026-06 | Grupos nuevos: LAMBDA, NEW BETTA, GDA USIL (detectados automáticamente desde el Sheet) |
| 2026-06 | Fix tooltip gráfico de evolución (% asistencia al hacer hover) |
| 2026-06 | GROUP_START_DATES aplicado a sesiones_por_grupo → columna Sesiones correcta para grupos nuevos |
| 2026-06 | persona_key incluye DNI → personas con mismo nombre se cuentan correctamente (303→305) |
| 2026-06 | Fix tooltip mini-chart modal de grupo; altura charts overview sincronizada |
| 2026-06 | Excepción 30/5: GDC BETTA VIAJEROS no tuvo sesión |
| 2026-06 | Regla FECHA_INGRESO y GROUP_START_DATES: cuentan desde la fecha misma (inclusive), no desde el sábado siguiente |
| 2026-06 | GROUP_START_DATES LAMBDA y NEW BETTA: fecha actualizada a 16/05 → 4 sesiones (16/5, 23/5, 30/5, 06/6) |
| 2026-06 | Evento El Viaje (16/05) registrado |
| 2026-06 | Excepción 6/6: GDC BETTA no tuvo sesión |
| 2026-07 | GDC BETTA VIAJEROS en hold desde 27/6 (GROUP_END_DATES) |
| 2026-07 | Excepción 4/7: GDC LAMBDA y GDC SIGMA no tuvieron sesión (por acuerdo) |
| 2026-07 | Evento Puentes (20/06) registrado |
| 2026-07 | Refactor: separación persona/grupo/global. GROUP_START_DATES ya no afecta el historial ni % individual, solo la métrica del grupo. Fix: clave GDC NEW BETTA → GDC OMEGA (el grupo se renombró y la regla dejó de aplicarse) |
| 2026-07 | Reorg de grupos GDA/GDC: rename `GDA USIL [TBD]` → `GDA USIL` (mismo grupo, sin cambio de código — ningún nombre de grupo está hardcodeado en `process_data.py`, todo viene de `GRUPO_ACTUAL` dinámicamente). `GDC EPSILON` y `GDA FAITH` se disolvieron intencionalmente y sus miembros se redistribuyeron entre otros grupos existentes (DELTA, LAMBDA, PHI, USIL, HOLY, SIGMA, ULIMA, entre otros). Aparecen dos grupos nuevos, `GDC ETA` y `GDA ULIMA`, formados con gente que ya llevaba tiempo en J1 (no cohortes nuevas) — por decisión del usuario, **no** se les agrega entrada en `GROUP_START_DATES`: sus sesiones de grupo cuentan desde el inicio del ciclo igual que los grupos históricos, y cada persona sigue limitada por su propia `FECHA_INGRESO` como siempre. |
| 2026-07-23 | Eventos EJEC (11/07) y Reencuentro EJEC (18/07) registrados en `EVENTS` — esas fechas tenían asistencia baja inicial porque el Sheet no estaba completo al momento del fetch; al recargarse, la asistencia subió a niveles normales y ahora aparecen marcadas como evento en el gráfico de evolución. |
