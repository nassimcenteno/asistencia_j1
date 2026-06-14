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

## 10. Fecha de inicio de grupos (GROUP_START_DATES)

Algunos grupos fueron creados durante el ciclo y no existían desde el inicio. Estos grupos tienen una fecha de inicio codificada en `GROUP_START_DATES` en `process_data.py`. Las sesiones anteriores a esa fecha no cuentan para sus miembros, no afectan la evolución global, y la columna **Sesiones** en la tabla de grupos refleja solo las sesiones desde ese punto (inclusive).

| Grupo | Fecha de creación | Active from |
|---|---|---|
| GDC LAMBDA | 16/05/2026 | 16/05/2026 |
| GDC NEW BETTA | 16/05/2026 | 16/05/2026 |

Aplicación en el código:
- `group_af_map` se computa antes del loop de filas y se usa en `aplica_denominador` (numerador)
- `sesiones_por_grupo` también aplica `group_af_map` al construirse → `sesiones_totales` correcto en tabla de grupos
- `person_active_from` en la evolución combina GROUP_START_DATES + FECHA_INGRESO personal (safeguard doble)

Al agregar un nuevo grupo con fecha de inicio: actualizar `GROUP_START_DATES` en `process_data.py` Y esta tabla.

---

## 11. Fecha de ingreso individual (FECHA_INGRESO)

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
