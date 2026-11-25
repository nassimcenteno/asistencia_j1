# Dashboard de asistencia J1 (generado por GitHub Actions)

Este repositorio publica el dashboard en GitHub Pages. **Solo contiene código**: los datos se leen de Google Drive en cada ejecución.

- **Cuándo corre:** lunes y martes a las 9 a. m. y miércoles a las 2 a. m. (Lima; GitHub suele retrasarse varias horas), y a mano desde Actions → *Reporte Asistencia J1* → *Run workflow*.
  Con `publicar` desmarcado solo comprueba que lee el Fact y el maestro y que genera el dashboard (no publica nada).
- **Qué lee:** el Fact de asistencia (`J1_FACT_ASISTENCIA_ID` en `reporte.yml`) y el `Maestro_J1_AAAA-MM` más reciente de la carpeta de maestros, con la cuenta de servicio del secreto `GOOGLE_CREDENTIALS`
  (esa cuenta necesita acceso de **lector** al Fact y a la carpeta de maestros).
- **Reglas** (umbrales, quarters, grupos, calendario): están en las pestañas del Fact, no aquí. Cambiarlas ahí cambia el dashboard en la siguiente ejecución.
- **Privacidad:** los logs solo muestran conteos. El dashboard lleva nombres (no DNI), como el anterior.
- **Código:** copia generada desde el repo de trabajo (`tools/asistencia`, `tools/maestros`, `generador`); no se edita a mano aquí. Para cambiar el diseño o la lógica, se regenera el paquete.
