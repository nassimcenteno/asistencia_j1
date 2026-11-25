"""Asistencia v2 (tool general): las reglas de negocio de la asistencia, leídas de las tablas del modelo (nada hardcodeado).
Es el ÚNICO lugar donde viven las reglas: el motor las usa y el dashboard solo recibe `parametros` y datos ya resueltos.
Referencia de las reglas: projects/2026-11-18_asistencia_v2/inputs/legacy_sistema/workflows/lineamientos_reporte.md (sistema viejo, que se replica).
Tablas esperadas (listas de dicts): grupos, calendario, parametros.
"""
import datetime

from asistencia_modelo import id_grupo, lista

QUARTERS = ("Q1", "Q2", "Q3", "Q4")


def _fecha(s):
    s = (s or "").strip()
    return datetime.date.fromisoformat(s) if s else None


class Reglas:
    def __init__(self, grupos, calendario, parametros):
        self.grupos = {id_grupo(g["grupo"]): {**g, "nombre": g["grupo"]} for g in grupos}  # grupo_id (derivado del nombre) -> fila
        self.eventos = {c["sabado"]: c["evento"] for c in calendario if c["evento"].strip()}
        p = {x["parametro"]: x["valor"] for x in parametros}
        self.umbral_inconstante = float(p["inconstante_hasta_pct"])
        self.umbral_activo = float(p["activo_hasta_pct"])
        self.ventana_riesgo = int(p["riesgo_sesiones"])
        self.semana_parcial_max = int(p["semana_parcial_max_personas"])
        self.semana_en_curso_dias = int(p.get("semana_en_curso_dias", 0))  # la última sesión sigue "en curso" hasta N días después (los grupos aún registran)
        self.miembro_formal = set(lista(p["miembros_formales"]))
        self.quarters = [(q, _fecha(p[q.lower() + "_desde"]), _fecha(p[q.lower() + "_hasta"])) for q in QUARTERS]  # [(nombre 'Q1', inicio, fin|None)]
        self.viajeros = id_grupo(p.get("grupo_viajeros", ""))
        self.tipo_acreditado = p.get("tipo_que_cuenta_como_asistencia", "").strip()  # TIPO_GRUPO del maestro cuyos meses cuentan como asistidos ('8. Mentores'); vacío = regla apagada
        self.asistencia_manda = {gid for gid, g in self.grupos.items() if g["sesion_si_asiste_alguien"].strip().upper() == "SI"}
        self.inicio = {gid: _fecha(g["empieza_el"]) for gid, g in self.grupos.items() if g["empieza_el"].strip()}
        self.excepciones = {}  # fecha iso -> (modo 'solo'|'todos_menos', {grupo_id}); una fila sin grupos no restringe
        for c in calendario:
            solo, no = lista(c["se_reunen_solo"]), lista(c["no_se_reunen"])
            if solo and no:
                raise ValueError(f"calendario {c['sabado']}: usa se_reunen_solo o no_se_reunen, no ambas")
            if not (solo or no):
                continue
            ids = {id_grupo(n) for n in solo or no}
            desconocidos = [n for n in solo or no if id_grupo(n) not in self.grupos]
            if desconocidos:
                raise ValueError(f"calendario {c['sabado']}: grupo que no está en la pestaña grupos: {desconocidos}")
            self.excepciones[c["sabado"]] = ("solo" if solo else "todos_menos", ids)

    # ---- períodos y status ----
    def quarter(self, d):
        for nombre, ini, fin in self.quarters:
            if d >= ini and (fin is None or d <= fin):
                return nombre
        raise ValueError(f"La fecha {d} no cae en ningún quarter (revisar parametros)")

    def status(self, pct):
        """0 Inactivo · hasta el umbral Inconstante · hasta el umbral Activo · Fiel."""
        if pct == 0:
            return "Inactivo"
        if pct <= self.umbral_inconstante:
            return "Inconstante"
        if pct <= self.umbral_activo:
            return "Activo"
        return "Fiel"

    # ---- sesiones ----
    def aplica_excepcion(self, fecha, gid):
        """False si la fecha tiene una excepción que deja fuera al grupo."""
        x = self.excepciones.get(fecha.isoformat())
        if not x:
            return True
        modo, gs = x
        return gid in gs if modo == "solo" else gid not in gs

    def hubo_sesion(self, gid, fecha, asistentes_grupo_fecha):
        """Grupos regidos por asistencia: hubo sesión solo si asistió al menos 1 persona esa fecha."""
        if gid in self.asistencia_manda:
            return asistentes_grupo_fecha.get((gid, fecha), 0) > 0
        return True

    def sesion_valida(self, fecha, gid, asistentes_grupo_fecha):
        return self.aplica_excepcion(fecha, gid) and self.hubo_sesion(gid, fecha, asistentes_grupo_fecha)

    def es_miembro(self, tipo_miembro):
        return (tipo_miembro or "") in self.miembro_formal
