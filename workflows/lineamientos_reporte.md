# Lineamientos del Reporte de Asistencia — J1

> **FUENTE DE VERDAD para todas las reglas de negocio.**
> Antes de modificar `process_data.py` o `dashboard_template.html`, leer este archivo.
> Cuando el usuario da un nuevo lineamiento permanente, agregarlo aquí Y al código.

---

## 1. Definición de Status (% asistencia individual)

| % Asistencia | Status |
|---|---|
| 0% | Inactivo |
| 1% – 40% | Inconstante |
| 41% – 74% | Activo |
| >74% | Fiel |

Fuente en código: `get_status()` en `process_data.py` y `statusFromPct()`/`pctColor()` en `dashboard_template.html` (los tres deben coincidir; `pctColor` usa el mismo corte: >74 verde, >40 azul, >0 ámbar). Se calcula sobre el total de sesiones que **aplican al grupo** (ver sección 4).

---

## 2. Períodos

| Período | Rango | Meses |
|---|---|---|
| **Q1** | 01/01 – 31/03 | Enero – Marzo (inclusive) |
| **Q2** | 01/04 – 31/07 | Abril – Julio (inclusive) |
| **Q3** | 01/08 – TBD | Agosto en adelante (sin fecha de cierre definida aún) |

Regla en código: `get_quarter()` en `process_data.py` — `month <= 3` → Q1, `month <= 7` → Q2, resto → Q3.
Los tres quarters se calculan y muestran en paralelo en todo el pipeline: campos `pct_q1/q2/q3`,
`asist_q1/q2/q3`, `total_q1/q2/q3`, `status_q1/q2/q3` por persona y `pct_q1/q2/q3` por grupo.
Cuando se defina el cierre de Q3 (o arranque Q4), actualizar `get_quarter()` y esta tabla.

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
| **04/07/2026** | GDC LAMBDA y GDC SIGMA **no** tuvieron sesión (por acuerdo) — excluir de su denominador. |

| **03/10/2026** | SOLO tuvo sesión GDC BETTA VIAJEROS. El resto NO cuenta esta fecha. |

Nota 03/10: BETTA VIAJEROS además se rige por la regla de asistencia (§12), así que mientras el Sheet no tenga ningún asistente cargado para esa fecha, la fecha queda fuera para todos (no hay denominador) y recién aparece cuando se cargue su asistencia. Las fechas que no aplican a nadie (`total_aplica = 0`) tampoco se emiten en `evolucion` (no se grafica un 0% falso).

**Regla por defecto:** Si una fecha no está en excepciones, aplica a TODOS los grupos.

**GDC BETTA y GDC BETTA VIAJEROS** ya no llevan excepciones manuales por fecha ni "hold": se rigen por la regla de asistencia de la sección 12 (0 asistentes en una fecha ⇒ no hubo sesión). Las excepciones manuales que tenían (02/05, 23/05, 30/05, 06/06) se eliminaron porque esa regla las cubre automáticamente y de forma retroactiva.

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
| **15/08/2026** | J-Fest |
| **05/09/2026** | Alaba |

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

1. **Nivel persona** (`total_sesiones`, `pct_total`, `historial`, `at_risk`, `racha_actual`, status): se basa **únicamente** en su propia `FECHA_INGRESO` (si la tiene) + `EXCEPTIONS` + regla de asistencia de grupos `ATTENDANCE_DRIVEN_GROUPS` (sección 12). **No aplica `GROUP_START_DATES`.** Refleja la trayectoria real de la persona, sin importar cómo se llama o cuándo se creó su grupo actual.
2. **Nivel grupo** (tabla de grupos: `sesiones_totales`, `pct_asistencia`, `pct_q1`, `pct_q2`, `pct_q3`): sí aplica `GROUP_START_DATES` (además de `EXCEPTIONS` y la regla de asistencia). Se calcula de forma independiente — **ya no es la suma de los totales de cada persona** — usando el flag interno `aplica_grupo` por sesión, que combina la fecha de inicio del grupo con la `FECHA_INGRESO` de cada miembro (lo que sea más tardío).
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
- `sesiones_por_grupo` (con `GROUP_START_DATES`) → `sesiones_totales` / `sesiones_qN` en la tabla de grupos
- `sesiones_por_grupo_persona` (sin `GROUP_START_DATES`) → historial y denominador de cada persona
- ambos filtran por `session_valid_for_group()` = `session_applies_to_group()` (EXCEPTIONS) **y** `group_had_session()` (regla de asistencia, sección 12)

Al agregar un nuevo grupo con fecha de inicio, o renombrar uno existente: actualizar `GROUP_START_DATES` en `process_data.py` Y esta tabla.

---

## 12. Grupos regidos por asistencia (ATTENDANCE_DRIVEN_GROUPS)

Para ciertos grupos, **la asistencia manda**: en cualquier fecha en que el grupo tenga **0 asistentes** se asume que **no hubo sesión** esa semana y esa fecha se excluye por completo (del denominador y numerador de sus miembros, del `sesiones_totales`/`sesiones_qN` del grupo y del `total_aplica` de la evolución semanal). Si en esa fecha hubo **al menos 1 asistente**, la sesión **sí cuenta**.

Es una regla **dinámica y retroactiva**: se recalcula en cada corrida desde los datos, no hay fechas hardcodeadas. **Reemplaza** al antiguo mecanismo de "hold" (`GROUP_END_DATES`) y a las excepciones manuales por fecha que estos grupos llevaban.

| Grupo |
|---|
| GDC BETTA |
| GDC BETTA VIAJEROS |

Aplicación en el código: `group_had_session()` (usa el mapa `group_attendance` que cuenta asistentes por grupo×fecha) dentro de `session_valid_for_group()` en `process_data.py`. Se usa en el post-proceso que marca `aplica_denominador`/`aplica_grupo` por sesión, en `sesiones_por_grupo(_persona)` y en `total_aplica` de la evolución.

**Cuidado:** si el Sheet aún no cargó la asistencia de una semana, esa fecha se verá como 0 y se excluirá temporalmente; vuelve a contar cuando se cargue. Es el tradeoff aceptado de esta regla.

Al sumar un grupo a esta regla: agregarlo a `ATTENDANCE_DRIVEN_GROUPS` en `process_data.py` (clave = `GRUPO_ACTUAL` en mayúsculas) Y a esta tabla.

---

## 13. Fecha de ingreso individual (FECHA_INGRESO)

Si una persona tiene la columna `FECHA_INGRESO` con un valor, sus sesiones **solo cuentan desde esa fecha en adelante (inclusive)**.

- Sesiones previas a esa fecha: no afectan su numerador, ni su denominador, ni el `total_aplica` de la evolución semanal del grupo.
- Si la fecha de ingreso no coincide con una fecha de sesión, la primera sesión aplicable es la primera fecha de sesión >= `FECHA_INGRESO`.

**Ejemplo:** Ingreso el 16/05/2026 (sábado) → `active_from` = 16/05/2026. Cuenta sesiones desde el 16/5 en adelante.
**Ejemplo:** Ingreso el 17/05/2026 (domingo) → `active_from` = 17/05/2026. Primera sesión aplicable: 23/05/2026.

Al agregar personas nuevas con FECHA_INGRESO: no requiere cambio de código. El pipeline lo detecta automáticamente desde la columna del Sheet.

---

## 14. Proyectos (J1 / Proyecto Betta) — solo presentación

El dashboard tiene un toggle **Proyecto** (J1 / Betta, combinables, mínimo 1; default ambos). **Proyecto Betta** = `GDC BETTA`, `GDA GAMMA`, `GDC BETTA VIAJEROS`, `GDC OMEGA` (`PROYECTO_BETTA_GROUPS` en `process_data.py`); **J1** = todos los demás grupos. `process_data.py` solo etiqueta `proyecto` ('betta'|'j1') en cada persona y grupo; **no cambia ningún cálculo de asistencia**. Con un solo proyecto, el dashboard recalcula en cliente (`buildView()`) KPIs, tipos, evolución semanal y riesgo desde las personas filtradas; con ambos usa el JSON tal cual. La clave debe coincidir con `GRUPO_ACTUAL` (si renombran un grupo, pasa a J1 sin error — misma advertencia que §11).

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
| 2026-09-10 | **Se agrega Q3.** Q1: 01/01–31/03, Q2: 01/04–**31/07** (antes "abril en adelante"), Q3: 01/08–TBD. `get_quarter()` ahora es de 3 ramas. Todo el pipeline calcula y muestra los 3 quarters en paralelo: tabla Personas (columna Q3%), chart "Comparativa por Quarter por Grupo" (3 series), modal de persona (4ª tarjeta Q3 + mini-chart). La matriz "Cambios de Status" pasó a tener un **selector de transición** (Q1→Q2 / Q2→Q3 / Q1→Q3). El sub-agente `sub_insights` también: semáforo con Q3% y Δ Q2→Q3, sección Momentum con dos matrices (Q1→Q2 y Q2→Q3), columna vertebral y nuevos ingresos con Q3%. Además se eliminó el `status_matrix` que `process_data.py` emitía en el JSON — era código muerto (el dashboard y el sub-agente recalculan la matriz client-side desde `status_q*`). |
| 2026-09-10 (2) | **Filtro global de período** en el dashboard: chips Q1/Q2/Q3 **combinables** (mín. 1) a la altura de las pestañas, a la derecha. Afecta a TODAS las pestañas y gráficos: KPIs (% asistencia, status dist), ranking, evolución semanal, tabla y ranking de grupos, tabla de personas (columna "Total%" y status), export CSV. **Con los 3 Q activos (default) NADA se recalcula** — los helpers `scoped*()` hacen `return DATA.*` tal cual, así que los números son idénticos a antes del filtro (regla: el drift 294→292 fue un bug de una versión intermedia, corregido). **Excepciones al filtro:** (a) la dona "Distribución por tipo" es puramente poblacional, no depende del período; (b) "En Riesgo" sigue siendo global (últimas 4 sesiones del ciclo) aunque el % por fila sí refleja el período; (c) la matriz "Cambios de Status" NO obedece el filtro global — tiene su propio selector de transición; (d) "Participantes" y "% membresía" se mantienen sobre el roster completo (292/294 personas nunca se mueven por el filtro). `process_data.py` expone conteos por-quarter de grupo (`asist_qN`, `posibles_qN`, `sesiones_qN`) para combinar quarters con sumas. Se eliminó el `<select>` per-tabla `filterGrupoQ` (redundante). |
| 2026-09-10 (4) | **GDC BETTA y GDC BETTA VIAJEROS pasan a regla de asistencia** (nueva sección 12). Se eliminó `GROUP_END_DATES` / `session_before_group_end()` (el hold de BETTA VIAJEROS desde 27/6) y las 4 excepciones manuales por fecha de BETTA (02/05, 23/05, 30/05, 06/06). Nuevo: `ATTENDANCE_DRIVEN_GROUPS = {"GDC BETTA", "GDC BETTA VIAJEROS"}` + `group_had_session()` sobre el mapa `group_attendance` (asistentes por grupo×fecha). En una fecha con 0 asistentes ⇒ no hubo sesión (retroactivo y hacia adelante). El cálculo de `aplica_denominador`/`aplica_grupo` se movió del loop de filas a un post-proceso porque ahora necesita el mapa de asistencia completo. Efecto: BETTA VIAJEROS pasó de ~16 a 17 sesiones (recuperó semanas post-27/6 donde sí hubo gente: 11/7, 18/7, 22/8, 5/9) y BETTA de ~23 a 22. **El dashboard no necesitó cambios** — todo sale de `process_data.py` y el dashboard solo presenta. |
| 2026-09-10 (3) | **Filtro de período local en los pop-ups.** El modal de persona y el de grupo tienen su propia fila de chips Q1/Q2/Q3 (`modalQBar()`), independiente del filtro global, que arranca copiando el estado global al abrir. Persona: recalcula la tarjeta de selección (4ª, con outline morado, label = quarters elegidos, ej. "Q2+Q3"), filtra el historial y ajusta el mini-chart. Grupo: recalcula las tarjetas de status, el "N sesiones", el chart de evolución y el ranking de menor asistencia. `openDrilldown`/`openGroupDrilldown` ahora solo hacen setup; el cuerpo lo arman `renderPersonModal()`/`renderGroupModal()` para poder re-renderizar al togglear. Eventos nuevos: **J-Fest (15/08)** y **Alaba (05/09)**. Rediseño: el chart de evolución del modal de grupo usa el estilo del de evolución total (área con gradiente, marcadores, línea de promedio); el mini-chart Q por persona perdió el eje Y. |
| 2026-10-08 (2) | **Parche en `fetch_sheets_data.py`:** si `02. Imp_Asistencia` tiene una asistencia (fecha+DNI) que `03. Asistencia_Reporting` dejó en 0 (pasa cuando `KEY_FECHA_DNI` de 02 quedó vacía por fórmula sin arrastrar) se corrige al vuelo y se avisa por consola. Detectó 16 filas: 3 de BETTA VIAJEROS del 03/10 y 13 del 26/09 (LAMBDA 7, ETA 6). **Modal de grupo:** promedio de evolución ponderado (Σasistentes/Σposibles), % semanales con 1 decimal, aviso en tooltip de miembros sin ingreso, margen superior en el chart. |
| 2026-10-08 | **Umbrales de status alineados al código:** Fiel >74%, Activo 41–74%, Inconstante 1–40% (la doc decía 80/51/50 y `pctColor` del dashboard usaba 80/51). **Excepción 03/10:** solo GDC BETTA VIAJEROS tuvo sesión. **Toggle de proyecto J1 / Betta** (§14). `evolucion` ya no emite fechas con `total_aplica = 0`. |
