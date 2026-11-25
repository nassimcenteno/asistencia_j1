"""Maestros mensuales (tool general)
Reglas de formato y utilidades PURAS (sin Drive ni archivos) compartidas por todas las tools de maestros:
vocabulario, fechas y edades, Nombre Propio, orden de filas y estándar visual. Una sola definición de cada regla.
"""
import re
import datetime
import calendar
import unicodedata

# ---- vocabulario ------------------------------------------------------------------------------
ACTIVOS = {"1. GBU", "2. GDA", "3. GDC", "8. Mentores", "9. Pastor"}
FECHAS = ("FECHA_INGRESO", "FECHA_NACIMIENTO", "FECHA_BAUTIZO_TRANSF")
FORMULAS = ("EDAD", "CATEGORIA_EDAD", "CATEGORIA")
COLUMNAS_NOMBRE_PROPIO = ("URBANIZACION", "COLEGIO", "CARRERA")
TIPOS = ["1. GBU", "2. GDA", "3. GDC", "4. Link J1", "5. Viaje", "6. J2", "7. Desconectado", "8. Mentores", "9. Pastor"]
ROLES = ["Participante", "Mentor", "Comentor", "Pastor"]
TIPOS_MIEMBRO = ["Miembro Bautizado", "Transferido"]
PARTICULAS_APELLIDO = {"de", "del", "la", "las", "los", "y", "san", "santa", "da", "di", "van", "von", "mac", "el"}

# ---- estándar visual de las hojas ---------------------------------------------------------------
FUENTE, TAM, VERDE_HEX = "Century Gothic", 7, "15452F"


# ---- texto ------------------------------------------------------------------------------------
def norm(s):
    """Minúsculas, sin tildes y con espacios simples: para comparar y ordenar sin distinguir acentos."""
    s = unicodedata.normalize("NFD", "" if s is None else str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


CONECTORES = {"de", "del", "la", "las", "los", "el", "y", "en", "al", "con", "por", "para"}
SIGLAS = {"LMCS", "FAP", "UCT", "COAR", "NA", "UPC", "USIL", "ULIMA", "PUCP", "UNI", "UNMSM", "ESAN", "UCSUR", "UPN", "UTP", "USMP",
          "URP", "UPCH", "UNFV", "UNAC", "UNALM", "UCV", "UARM", "UCSS", "UPSJB", "UCAL", "UCSM", "SENATI", "TECSUP", "IDAT", "CIBERTEC",
          "IE", "IEP"}
_ROMANO = re.compile(r"^(?=[IVX])X{0,3}(IX|IV|V?I{0,3})$")  # I a XXXIX; sin M, D, C, L para no confundir con palabras (Mi, Di, Li)
_PALABRA = re.compile(r"[^\W\d_]+")


def nombre_propio(x):
    """Nombre Propio como valor (no fórmula): cada palabra con inicial mayúscula y el resto en minúscula, salvo
    - siglas (lista SIGLAS), numerales romanos (II, XXIII) e iniciales con punto (I.E.): todo en mayúsculas;
    - conectores (de, la, y, ...): minúscula, salvo que sean la primera palabra del texto;
    - sufijos ordinales pegados a un número (2da, 1ro): minúscula.
    Idempotente: aplicarlo dos veces da lo mismo."""
    if not isinstance(x, str):
        return x
    estado = {"primero": True}

    def palabra(m):
        t, u = m.group(0), m.group(0).upper()
        es_primero, estado["primero"] = estado["primero"], False
        previo = x[m.start() - 1] if m.start() else ""
        siguiente = x[m.end()] if m.end() < len(x) else ""
        if previo.isdigit():
            return t.lower()
        if u in SIGLAS or _ROMANO.match(u) or (len(t) == 1 and siguiente == "."):
            return u
        if t.lower() in CONECTORES and not es_primero:
            return t.lower()
        return t[:1].upper() + t[1:].lower()

    return _PALABRA.sub(palabra, x)


def split_nombre(full):
    """Separa NOM_COMPLETO en (NOMBRES, APELLIDOS): los 2 últimos apellidos, con partículas (de la, del...).
    Acierta 98,6% contra el maestro actual."""
    t = re.sub(r"\s+", " ", str(full)).strip().split(" ")
    if len(t) <= 1:
        return " ".join(t), ""
    if len(t) == 2:
        return t[0], t[1]

    def inicio(fin):
        i = fin
        while i - 1 >= 1 and t[i - 1].lower() in PARTICULAS_APELLIDO:
            i -= 1
        return i
    i2 = inicio(len(t) - 1)
    i1 = inicio(i2 - 1) if i2 - 1 >= 1 else i2
    if i1 < 1:
        i1 = i2
    return " ".join(t[:i1]), " ".join(t[i1:])


# ---- fechas, edad y categorías ----------------------------------------------------------------
_EPOCA = datetime.date(1899, 12, 30)


def serial(d):
    """Fecha -> número de serie de Sheets/Excel."""
    return (d - _EPOCA).days


def from_serial(n):
    return _EPOCA + datetime.timedelta(days=int(n))


def month_end(ym):
    y, m = map(int, ym.split("-"))
    return datetime.date(y, m, calendar.monthrange(y, m)[1])


def months(desde, hasta):
    """Genera 'AAAA-MM' de `desde` a `hasta`, ambos incluidos."""
    y, m = map(int, desde.split("-"))
    yb, mb = map(int, hasta.split("-"))
    while (y, m) <= (yb, mb):
        yield f"{y}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def categoria_edad(edad):
    return "<18" if edad <= 18 else "18-21" if edad <= 21 else "21-24" if edad <= 24 else "25+"


def edad_al(nacimiento_serial, corte):
    """(edad con 2 decimales, categoría) a la fecha de corte. Igual a la fórmula viva del vigente."""
    edad = round((serial(corte) - nacimiento_serial) / 365.25, 2)
    return edad, categoria_edad(edad)


def categoria(tipo_grupo):
    """CATEGORIA según TIPO_GRUPO (misma lógica que la fórmula viva del vigente)."""
    if tipo_grupo in ("", None):
        return ""
    return "1. ACTIVO J1" if tipo_grupo in ACTIVOS else "2. INACTIVO"


# ---- orden de filas ---------------------------------------------------------------------------
def orden_key(r):
    """Jerarquía: TIPO_GRUPO, GRUPO_ACTUAL (vacíos al final), mentores primero (ROL_ACTUAL = Mentor), NOM_COMPLETO.
    Sin distinguir tildes ni mayúsculas."""
    def fin(x):
        return norm(x) if x not in ("", None) else "￿"
    return (r.get("TIPO_GRUPO") or "￿", fin(r.get("GRUPO_ACTUAL")), 0 if r.get("ROL_ACTUAL") == "Mentor" else 1,
            norm(r.get("NOM_COMPLETO", "") or ""))
