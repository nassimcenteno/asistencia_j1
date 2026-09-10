"""
Tool: generate_dashboard.py
Inyecta .tmp/asistencia_processed.json en tools/dashboard_template.html
y escribe .tmp/dashboard.html (dashboard interactivo — Tailwind + ApexCharts).

Toda la UI (HTML/CSS/JS) vive en dashboard_template.html. Este script solo
reemplaza el marcador PLACEHOLDER por el JSON procesado, serializado en una
sola línea, dentro de `const DATA = ...;`.
"""
import json
import os
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"
TEMPLATE_PATH = Path(__file__).parent / "dashboard_template.html"
OUTPUT_PATH = TMP_DIR / "dashboard.html"
PLACEHOLDER = "__ASISTENCIA_DATA__"


def main():
    processed_path = TMP_DIR / "asistencia_processed.json"
    if not processed_path.exists():
        print("[ERROR] .tmp/asistencia_processed.json no encontrado. Ejecuta primero process_data.py")
        sys.exit(1)
    if not TEMPLATE_PATH.exists():
        print(f"[ERROR] Falta el template: {TEMPLATE_PATH}")
        sys.exit(1)

    data = json.loads(processed_path.read_text(encoding="utf-8"))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if template.count(PLACEHOLDER) != 1:
        print(f"[ERROR] El template debe contener {PLACEHOLDER} exactamente 1 vez "
              f"(encontrado {template.count(PLACEHOLDER)}).")
        sys.exit(1)
    html = template.replace(PLACEHOLDER, json.dumps(data, ensure_ascii=False))
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    print(f"[OK] dashboard.html generado en: {OUTPUT_PATH}")
    if not os.getenv("CI"):
        print("[...] Abriendo en el browser...")
        webbrowser.open(OUTPUT_PATH.as_uri())


if __name__ == "__main__":
    main()
