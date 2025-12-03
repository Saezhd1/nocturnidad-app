from datetime import datetime

def _parse_hhmm(s, base_date=None):
    """
    Convierte una cadena HH:MM en datetime.
    - Si la hora es >= 24, se convierte en hora del día siguiente.
    - El campo 'fecha' del registro se mantiene igual (la del PDF).
    """
    try:
        h, m = s.split(":")
        h = int(h); m = int(m)

        if 0 <= m <= 59:
            if h >= 24:
                # Ajuste: horas extendidas -> día siguiente
                dt = datetime.strptime(f"{h-24:02d}:{m:02d}", "%H:%M")
                return dt + timedelta(days=1)
            elif 0 <= h <= 23:
                return datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M")
    except Exception:
        return None
    return None

def _tarifa_por_fecha(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
    except:
        f = datetime.today()
    return 0.05 if f <= datetime(2025, 4, 25) else 0.062

def _minutos_nocturnos(hi_dt, hf_dt):
    """
    Calcula minutos en tramos nocturnos:
    - 22:00 a 24:59
    - 04:00 a 06:00
    """
    minutos = 0
    tramos = [
        (datetime.strptime("22:00", "%H:%M"), datetime.strptime("24:59", "%H:%M")),
        (datetime.strptime("04:00", "%H:%M"), datetime.strptime("06:00", "%H:%M")),
    ]
    for ini, fin in tramos:
        if hi_dt <= fin and hf_dt >= ini:
            o_ini = max(hi_dt, ini)
            o_fin = min(hf_dt, fin)
            if o_ini < o_fin:
                minutos += int((o_fin - o_ini).total_seconds() / 60)
    return minutos

def calcular_nocturnidad_por_dia(registros):
    """
    Calcula minutos nocturnos y el importe por cada día.
    La fecha mostrada siempre es la original del PDF.
    """
    resultados = []
    for r in registros:
        hi_dt = _parse_hhmm(r["hi"])
        hf_dt = _parse_hhmm(r["hf"])
        if not hi_dt or not hf_dt:
            continue

        minutos = _minutos_nocturnos(hi_dt, hf_dt)
        tarifa = _tarifa_por_fecha(r["fecha"])

        resultados.append({
            "fecha": r["fecha"],   # se mantiene la fecha original
            "hi": r["hi"],
            "hf": r["hf"],
            "minutos_nocturnos": minutos,
            "importe": f"{minutos * tarifa:.2f}",
            "principal": r.get("principal", True)
        })
    return resultados



