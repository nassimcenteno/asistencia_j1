# SOP — Sub-Agente: sub_insights

## Qué hace este sub-agente

Analiza el reporte de asistencia J1 en profundidad y produce insights que el dashboard no puede mostrar directamente: momentum individual Q1→Q2, alertas críticas agrupadas, impacto de eventos, análisis por rol, columna vertebral, nuevos ingresos y semáforo de grupos.

---

## Cuándo invocar

Invocar cuando el usuario pida:
- "análisis profundo / insights / deep dive"
- "qué está pasando en el grupo X"
- "quiénes están en riesgo"
- "cómo cambió la asistencia de Q1 a Q2"
- "quiénes son los más comprometidos / los más ausentes"
- "cómo impactaron los eventos"
- cualquier pregunta analítica que requiera comparaciones o drill-downs

---

## Prerequisito

Que exista `.tmp/asistencia_processed.json` (el pipeline ya debe haberse corrido con `python tools/run_report.py`).

---

## Cómo invocar (pasos exactos)

```
1. python subagents/sub_insights/analyze.py
   → El script genera insights_report_YYYY-MM-DD.md y .html con la fecha del día
   → Abre el HTML automáticamente en el browser
2. Leer: subagents/sub_insights/reports/insights_report_YYYY-MM-DD.md
   (usar glob o leer el archivo más reciente de la carpeta reports/)
3. Presentar los hallazgos más relevantes directamente en el chat
   — No volcar el .md crudo. Extraer insights, redactar respuesta clara.
   — Si la pregunta es general: top 3-5 hallazgos más llamativos.
   — Si la pregunta es específica: ir directo a la sección relevante.
```

Claude NO lee `asistencia_processed.json` directamente — ese archivo es grande.
Claude solo lee el `insights_report_*.md` del día (~17 KB) para razonar.

**Archivos fechados:** cada ejecución genera `insights_report_YYYY-MM-DD.md` y `.html`.
Los archivos anteriores se conservan en `reports/` — nunca se sobreescriben.

---

## Secciones disponibles en el reporte

| # | Sección | Cuándo usar |
|---|---------|-------------|
| 0 | KPIs Globales | Resumen rápido del ciclo |
| 1 | Semáforo de Grupos | Comparar grupos, ver cuáles subieron/bajaron |
| 2 | Momentum Q1→Q2 | Entender retención/churn individual entre quarters |
| 3 | Columna Vertebral | Identificar los más comprometidos del ciclo |
| 4 | Alertas Críticas | Ver quiénes necesitan atención pastoral urgente |
| 5 | Impacto de Eventos | Evaluar si los eventos especiales movieron la aguja |
| 6 | Sesiones más Débiles | Detectar patrones de baja asistencia en fechas específicas |
| 7 | Análisis por Rol | Ver compromiso de mentores vs comentores vs discípulos |
| 8 | Nuevos Ingresos | Evaluar cómo arrancaron los que ingresaron en el ciclo |

---

## Notas de interpretación (no alucinar contexto)

- **Delta Q2 negativo en LAMBDA / NEW BETTA**: esperado. Son grupos creados el 16/05, solo tienen sesiones desde esa fecha. Su denominador Q2 es menor → % puede parecer bajo vs grupos con todo el ciclo.
- **pct_q1 = "—" en grupos nuevos**: correcto, no tenían sesiones en Q1.
- **Momentum matrix**: solo incluye personas con sesiones en AMBOS quarters. Personas con solo Q2 (nuevos ingresos tardíos) NO aparecen.
- **Racha positiva**: sesiones consecutivas asistidas. Racha negativa: sesiones consecutivas ausentes.
- **at_risk**: definido como 0 asistencias en las últimas 4 sesiones que aplican al grupo. Es dinámico.

---

## Cómo responder

No volcar el reporte completo. Extraer solo las secciones relevantes a la pregunta del usuario y presentarlas con contexto interpretativo. Si la pregunta es general, presentar los 3-4 hallazgos más llamativos.

---

## Qué NO hace este sub-agente

- No modifica ningún dato
- No toca el pipeline productivo (`tools/`)
- No reemplaza el dashboard
- No genera alertas automáticas ni envía notificaciones
