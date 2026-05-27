"""
Orquestador principal — el único script que necesitas ejecutar.
Secuencia: fetch_sheets_data → process_data → generate_dashboard
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOOLS = ROOT / "tools"


def run_tool(script_name: str) -> bool:
    print(f"\n{'-'*50}")
    print(f">>  {script_name}")
    print(f"{'-'*50}")
    result = subprocess.run(
        [sys.executable, str(TOOLS / script_name)],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print(f"\n[ERROR]  {script_name} falló (exit code {result.returncode})")
        return False
    return True


def main():
    print("=" * 50)
    print("  REPORTE DE ASISTENCIA J1 — ALIANZA MONTERRICO")
    print("=" * 50)

    steps = [
        "fetch_sheets_data.py",
        "process_data.py",
        "generate_dashboard.py",
    ]

    for step in steps:
        if not run_tool(step):
            print("\n[STOP] Pipeline interrumpido. Revisa el error y vuelve a ejecutar.")
            sys.exit(1)

    print("\n[OK]  Reporte generado exitosamente.")


if __name__ == "__main__":
    main()
