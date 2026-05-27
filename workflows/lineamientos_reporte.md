# Lineamientos del Reporte de Asistencia — J1

> **FUENTE DE VERDAD para todas las reglas de negocio.**
> Antes de modificar `process_data.py`, leer este archivo.
> Cuando el usuario da un nuevo lineamiento permanente, agregarlo aquí Y al código.

---

## 1. Definición de Status (% asistencia individual)

| % Asistencia | Status |
|---|---|
| 0% | Inactivo |
| 1% – 50% | Inconstante |
| 51% – 79% | Activo |
| 80%+ | Fiel |

Se calcula sobre el total de sesiones que **aplican al grupo** (ver excepciones de fechas).

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
Cuando se agrega una nueva excepción, actualizarla aquí Y en `EXCEPTIONS` en `process_data.py`.

| Fecha | Regla |
|---|---|
| **11/04/2026** | SOLO tuvieron sesión: GDC BETTA, GDC BETTA VIAJEROS, GDC SIGMA. El resto NO cuenta esta fecha en su denominador. |
| **02/05/2026** | GDC BETTA **no** tuvo sesión — excluir de su denominador. |
| **23/05/2026** | GDC BETTA **no** tuvo sesión — excluir de su denominador. |

**Regla por defecto:** Si una fecha no está en excepciones, aplica a TODOS los grupos.

---

## 5. Eventos especiales (cuentan como sesión)

Estos no son sesiones regulares pero sí cuentan en el % de asistencia.
Aparecen destacados en el gráfico de evolución (punto naranja).

| Fecha | Evento |
|---|---|
| **28/02/2026** | JADAK |
| **14/03/2026** | Montecamp |
| **21/03/2026** | Reencuentro Montecamp |

---

## 6. Definición de "En Riesgo"

Una persona está **en riesgo** si tiene **0 asistencias en las últimas 4 sesiones** que aplican a su grupo.

El cálculo es **dinámico**: toma automáticamente las 4 fechas más recientes del historial de cada grupo. No requiere actualización manual.

---

## 7. Reglas de inclusión de personas

- Solo se incluyen personas con **GRUPO ACTUAL** no vacío.
- Vacío en GRUPO ACTUAL = persona desconectada = no aparece en el reporte.
- Se usa la columna `GRUPO ACTUAL`, NO la columna `GRUPO`.

---

## 8. Membresía formal

Los tipos de miembro que se consideran **miembros formales**:
- `Miembro Bautizado`
- `Transferido`

Cualquier otro valor (o vacío) = no es miembro formal.

---

## Historial de cambios

| Fecha | Cambio | Quién lo indicó |
|---|---|---|
| 2026-05 | Setup inicial del proyecto | nassimcenteno |
| 2026-05 | Excepciones 11/4, 2/5, 23/5 codificadas | nassimcenteno |
| 2026-05 | Eventos JADAK, Montecamp, Reencuentro registrados | nassimcenteno |
