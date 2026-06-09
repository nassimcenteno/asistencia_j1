# 🎨 WEB DESIGN & UI/UX SKILLS

Este documento define las capacidades y estándares de diseño que el agente debe aplicar para generar interfaces web profesionales, dashboards de analítica y reportes interactivos.

## 🛠️ CORE DESIGN STACK
- **Framework:** Tailwind CSS (via CDN para prototipado rápido y despliegue en Railway).
- **Iconografía:** Lucide Icons o FontAwesome 6.
- **Gráficos:** ApexCharts.js o Chart.js (Interacción fluida y responsiva).
- **Tipografía:** Inter o Geist Sans (Modernas, legibles, profesionales).

## 🧠 DESIGN CAPABILITIES (SKILLS)

| Skill | Método de Ejecución | Resultado Esperado |
| :--- | :--- | :--- |
| **Atomic Layout Design** | Uso de Flexbox/Grid de Tailwind | Estructuras 100% responsivas y alineadas. |
| **Data Visualization** | Inyección de JSON en ApexCharts | Gráficos limpios con tooltips y paletas de colores BI. |
| **Component Architect** | Modularización en `tools/` | Secciones reusables (Cards, Tables, Navbars). |
| **Dark/Light Mode** | Clases `dark:` de Tailwind | Soporte nativo para temas de usuario. |
| **UX Flow** | Jerarquía de información | Los KPIs más importantes siempre van en el "Above the fold". |

## 📐 ESTÁNDARES VISUALES (REGLAS DE ORO)

1. **Dashboard Layout:**
   - **Header:** Título del reporte, selector de fechas y estado de conexión.
   - **Top Row (KPIs):** 3 o 4 tarjetas con métricas clave (ej: % Asistencia, Alertas, Total).
   - **Middle Row (Gráficos):** Tendencia semanal o distribución de datos.
   - **Bottom Row (Data Table):** Tabla detallada con búsqueda y filtros.

2. **Estética Profesional:**
   - **Espaciado:** Uso generoso de `gap` y `padding`. No amontonar elementos.
   - **Bordes:** `rounded-xl` o `rounded-2xl` para un look moderno de app.
   - **Soporte Visual:** Uso de estados `hover:` en botones y filas de tablas.

3. **Optimización de Assets:**
   - No descargar archivos locales a menos que se pida; priorizar CDNs oficiales para mantener el despliegue ligero.

## 🚀 PROMPT DE ACTIVACIÓN PARA DISEÑO
> "Usa el estándar de SKILLS.md para diseñar el `dashboard.html`. Prioriza una estética limpia estilo 'SaaS de Analytics', usa Tailwind CSS y asegúrate de que los gráficos de asistencia en `.tmp/asistencia_processed.json` sean interactivos."