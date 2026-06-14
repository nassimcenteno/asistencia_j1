# WEB DESIGN & UI/UX SKILLS

Este documento define los estándares de diseño que el agente debe aplicar para generar dashboards y reportes interactivos de nivel premium. Aplica a cualquier archivo HTML generado desde Python (f-string, single-file).

---

## Core Design Stack

- **CSS:** Tailwind CSS via CDN. Dark mode via CSS custom properties (`var(--bg)`, `var(--surface)`, `var(--text)`, `var(--muted)`, `var(--border)`), NO clases `dark:` de Tailwind — estas no funcionan en archivos HTML estáticos sin build step.
- **Gráficos:** ApexCharts.js (primario). Interacción fluida, gradientes, tooltips. Ver sección de patrones y limitaciones conocidas más abajo.
- **Iconografía:** SVG inline (Lucide-style: `stroke-width="1.5"`, `viewBox="0 0 24 24"`, `fill="none"`). No depender de CDN de icon fonts para que funcione offline y en single-file.
- **Tipografía:** Inter via Google Fonts (`font-family: 'Inter', sans-serif`). Pesos: 400, 500, 600, 700, 800.

---

## Layout y Estética

**Dashboard layout estándar:**
- Header con título, subtítulo y metadata (fecha, última actualización)
- Tab bar para navegación entre secciones
- Cards con `border-radius: 12-16px`, `background: var(--surface)`, `border: 1px solid var(--border)`
- KPI cards en grid de 4 columnas con icono en círculo de color semántico, valor grande, label, sub-label
- Gráficos en cards full-width o en grid 2 columnas

**Reglas de espaciado:**
- Padding de cards: `16px` mínimo, `20px` estándar
- Gap entre elementos: `12px` entre cards, `16-24px` entre secciones
- Prohibido amontonar — si hay riesgo de crowding, reducir font-size o agregar scroll, nunca comprimir el layout

**Estética SaaS:**
- Bordes `rounded-xl` o `border-radius: 12-16px` en contenedores
- `box-shadow` sutil en cards: `0 1px 3px rgba(0,0,0,.07)`
- Hover con `transition: background .15s ease`
- Colores semánticos: verde `#10B981` (positivo), rojo `#EF4444` (negativo), índigo `#4F46E5` (primario), celeste `#0EA5E9` (info), ámbar `#F59E0B` (alerta/evento)

---

## ApexCharts: Patrones y Limitaciones Conocidas

### Limitaciones críticas

**CSS variables no resuelven en canvas:**
`color: 'var(--muted)'` dentro de opciones de ApexCharts no funciona — el canvas no resuelve CSS custom properties. Siempre usar colores hex hardcodeados dentro de las opciones del chart.

**Labels de `annotations.yaxis` siempre se superponen:**
El label de una línea de referencia (`annotations.yaxis[].label`) siempre termina encima de datos o ejes, independientemente de `position` y `offsetY`. Solución: eliminar el label del objeto de anotación y crear un elemento HTML estático fuera del chart (ej. en el header de la card) con el mismo texto.

**`markers.colors` array no colorea puntos individuales:**
Pasar un array a `markers.colors` aplica el color a toda la serie, no punto a punto. Para colorear puntos individuales (ej. marcar eventos con naranja), usar `markers.discrete`:
```js
markers: {
  discrete: eventos.map((e, i) => e.evento ? {
    seriesIndex: 0, dataPointIndex: i,
    fillColor: '#F59E0B', strokeColor: '#D97706', size: 7
  } : null).filter(Boolean)
}
```

**Centro de donut vacío con `plotOptions.pie.donut.labels`:**
El API de labels internos del donut tampoco resuelve CSS variables y su posicionamiento es frágil. Solución: desactivar los labels internos (`show: false`) y superponer un `<div>` HTML con `position: absolute` centrado sobre el chart.

### Patrones recomendados

**Gradiente de área en line chart:**
```js
fill: {
  type: 'gradient',
  gradient: { type: 'vertical', shadeIntensity: 0, inverseColors: false,
               opacityFrom: 0.4, opacityTo: 0.02, stops: [0, 95, 100] }
}
```

**Línea de referencia (promedio):**
```js
annotations: {
  yaxis: [{ y: avg, borderColor: '#94A3B8', borderWidth: 1, strokeDashArray: 4 }]
}
// El label va en HTML, no en el objeto de anotación
```

**Donut sin labels internos + overlay HTML:**
```html
<div style="position:relative">
  <div id="chartTipos"></div>
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none">
    <div id="donutTotal" style="font-size:28px;font-weight:800;color:var(--text)"></div>
    <div style="font-size:12px;color:#64748B;margin-top:4px">personas</div>
  </div>
</div>
```

**Columnas verticales limpias (Q1 vs Q2):**
```js
chart: { type: 'bar' },
plotOptions: { bar: { horizontal: false, columnWidth: '60%' } },
dataLabels: { enabled: false },  // evita crowding de etiquetas
grid: { show: false },
xaxis: { labels: { rotate: -40, rotateAlways: true, style: { fontSize: '10px' } } }
```

---

## Python f-strings: Regla de Escaping

Todo el JS que va dentro de un f-string de Python requiere doblar las llaves:
- `{variable}` → solo para interpolación Python
- `{{literal}}` → se convierte en `{literal}` en el output HTML

Nunca usar backslashes dentro de expresiones f-string (genera SyntaxWarning). Si necesitas regex o caracteres especiales, usar variables intermedias fuera del f-string.

---

## KPI Cards con Icono

Patrón estándar para summary cards debajo de un chart:

```html
<div style="background:var(--surface2);border-radius:12px;padding:16px;text-align:center">
  <!-- Icono en círculo de color semántico -->
  <div style="display:flex;justify-content:center;margin-bottom:10px">
    <div style="width:32px;height:32px;border-radius:8px;background:#10B98118;display:flex;align-items:center;justify-content:center">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
           fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <!-- paths aquí -->
      </svg>
    </div>
  </div>
  <!-- Valor grande -->
  <div style="font-size:22px;font-weight:800;color:#10B981;line-height:1">85%</div>
  <!-- Label -->
  <div style="font-size:11px;font-weight:600;color:var(--text);margin-top:4px">Mejor semana</div>
  <!-- Sub-label -->
  <div style="font-size:10px;color:var(--muted);margin-top:2px">Sáb 14 mar</div>
</div>
```

El color del ícono, el valor grande, y el fondo del círculo (`color + '18'` para 10% opacidad) son siempre el mismo color semántico de la card.

---

## Prompt de Activación

> "Usa los estándares de `skills/DESIGN_SKILL.md` para diseñar el dashboard. Aplica el stack Tailwind + ApexCharts + dark mode via CSS custom properties. El JSON de datos está en `.tmp/asistencia_processed.json`."
