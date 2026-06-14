# 🎨 WEB DESIGN & UI/UX SKILLS (ULTRA-CHARGED)

Este documento define las capacidades y estándares de diseño de producto (UX/UI) que el agente debe aplicar de forma obligatoria para generar interfaces web profesionales, dashboards de analítica y reportes interactivos de nivel premium (estilo Stripe o Linear).

## 🛠️ CORE DESIGN STACK
- **Framework:** Tailwind CSS (via CDN para prototipado rápido y despliegue en Railway) con fuentes y temas extendidos.
- **Iconografía:** Lucide Icons o FontAwesome 6 (Estilo minimalista y consistente).
- **Gráficos:** ApexCharts.js o Chart.js (Interacción fluida, curvas smooth, gradientes de desvanecimiento y responsivos).
- **Tipografía:** Inter o Geist Sans (Modernas, legibles, profesionales, con tracking y pesos controlados).

## 🧠 DESIGN CAPABILITIES (SKILLS)

| Skill | Método de Ejecución | Resultado Esperado |
| :--- | :--- | :--- |
| **Atomic Layout Design** | Uso estricto de Flexbox/Grid de Tailwind (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`). | Estructuras 100% responsivas, alineadas y fluidas en cualquier dispositivo. |
| **Data Visualization** | Inyección matemática de JSON en ApexCharts anulando estilos por defecto. | Gráficos limpios con tooltips interactivos, líneas de guía sutiles y paletas de colores BI. |
| **Component Architect** | Modularización en `tools/` de componentes HTML limpios. | Secciones reusables con código limpio y mantenible (Cards, Tables, Navbars). |
| **Dark/Light Mode** | Clases `dark:` de Tailwind y manejo de fondos neutros modernos. | Soporte nativo para temas de usuario sin perder contraste ni jerarquía visual. |
| **UX Flow** | Jerarquía de información y arquitectura visual de datos. | Los KPIs más importantes siempre van en el "Above the fold" con indicadores de tendencia. |

## 📐 ESTÁNDARES VISUALES (REGLAS DE ORO REPOTENCIADAS)

1. **Dashboard Layout:**
   - **Header:** Título del reporte (`font-bold tracking-tight text-slate-900`), selector de fechas destacado y estado de conexión o sincronización.
   - **Top Row (KPIs):** 3 o 4 tarjetas premium (`bg-white border border-slate-100 shadow-sm shadow-slate-100/70 hover:shadow-md transition-all duration-200`) con métricas clave (ej: % Asistencia, Alertas, Total) acompañadas de badges de tendencia (`bg-emerald-50 text-emerald-700` o `bg-rose-50 text-rose-700`).
   - **Middle Row (Gráficos):** Tendencia semanal o distribución de datos usando curvas suaves (`curve: 'smooth'`), grosores estilizados (`width: 2.5`) y rellenos con gradientes limpios.
   - **Bottom Row (Data Table):** Tabla detallada envuelta en un bloque redondeado con aislamiento de desbordamiento (`overflow-hidden rounded-xl border border-slate-100`). Cabeceras en mayúsculas y texto pequeño (`text-xs font-semibold uppercase tracking-wider text-slate-400 bg-slate-50/75`). Filas con padding generoso (`px-6 py-4`) y efectos dinámicos de estado con badges estilizados.

2. **Estética Profesional SaaS:**
   - **Espaciado:** Uso generoso y matemático de `gap` y `padding` (dar "aire" a la lectura). Queda prohibido amontonar elementos o usar tablas nativas sin estilizar.
   - **Bordes:** `rounded-xl` o `rounded-2xl` en contenedores y componentes para un look moderno de aplicación web.
   - **Soporte Visual:** Uso obligatorio de estados `hover:` con transiciones suaves (`transition-all duration-200 ease-in-out`) en botones, enlaces y filas de tablas para mejorar la experiencia interactiva.
   - **Empty States:** Si la data viene vacía, la interfaz debe renderizar un contenedor centrado con un icono atenuado, un título descriptivo y un botón principal de acción clara.

3. **Optimización de Assets:**
   - No descargar archivos locales a menos que se pida; priorizar CDNs oficiales para mantener el despliegue ligero y la velocidad de carga al máximo.

## 🚀 PROMPT DE ACTIVACIÓN PARA DISEÑO
> "Usa el estándar de skills/DESIGN_SKILL.md para diseñar el `dashboard.html`. Prioriza una estética limpia estilo 'SaaS de Analytics', usa Tailwind CSS y asegúrate de que los gráficos de asistencia en `.tmp/asistencia_processed.json` sean interactivos."
