import pdfplumber
from datetime import datetime

# --- CONFIG ---
PRECIO_1 = 0.05   # €/min hasta 25/04/2025
PRECIO_2 = 0.062  # €/min desde 26/04/2025
FECHA_INICIO = datetime(2022, 3, 30)
FECHA_CAMBIO = datetime(2025, 4, 26)

def _in_range(xmid, xr, tol=2):
    return xr[0] - tol <= xmid <= xr[1] + tol

def _find_columns(page):
    words = page.extract_words(use_text_flow=True)
    fecha_x = hi_x = hf_x = None
    header_bottom = page.bbox[1] + 40
    for w in words:
        t = (w.get("text") or "").strip().lower()
        if t == "fecha":
            fecha_x = (w["x0"], w["x1"]); header_bottom = max(header_bottom, w["bottom"])
        elif t == "hi":
            hi_x = (w["x0"], w["x1"]); header_bottom = max(header_bottom, w["bottom"])
        elif t == "hf":
            hf_x = (w["x0"], w["x1"]); header_bottom = max(header_bottom, w["bottom"])
    if not (fecha_x and hi_x and hf_x):
        x0_page, x1_page = page.bbox[0], page.bbox[2]
        width = x1_page - x0_page
        fecha_x = (x0_page + 0.06 * width, x0_page + 0.22 * width)
        hi_x    = (x0_page + 0.69 * width, x0_page + 0.81 * width)
        hf_x    = (x0_page + 0.81 * width, x0_page + 0.95 * width)
    return {"fecha": fecha_x, "hi": hi_x, "hf": hf_x, "header_bottom": header_bottom}

def _normalize_hour(h):
    h = h.strip()
    if not h or ":" not in h:
        return h
    try:
        hh, mm = h.split(":")
        hh, mm = int(hh), int(mm)
    except ValueError:
        return h
    if hh == 0 and mm == 59:
        return "24:59"
    if hh >= 24:
        hh -= 24
        return f"{hh:02d}:{mm:02d}"
    return f"{hh:02d}:{mm:02d}"

def _to_minutes(h):
    if not h or ":" not in h:
        return None
    hh, mm = h.split(":")
    hh, mm = int(hh), int(mm)
    return hh * 60 + mm

def nocturnity_minutes(hi, hf):
    hi_min = _to_minutes(_normalize_hour(hi))
    hf_min = _to_minutes(_normalize_hour(hf))
    if hi_min is None or hf_min is None:
        return 0
    if hf_min < hi_min:
        hf_min += 24 * 60
    nocturnity_ranges = [
        (240, 360),    # 04:00–06:00
        (1320, 1440),  # 22:00–23:59
        (1440, 1500),  # 24:00–24:59
    ]
    total = 0
    for start, end in nocturnity_ranges:
        overlap_start = max(hi_min, start)
        overlap_end = min(hf_min, end)
        if overlap_end > overlap_start:
            total += overlap_end - overlap_start
    return total

def calcular_dinero(fecha_str, minutos):
    try:
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
    except Exception:
        return 0.0
    if fecha < FECHA_INICIO:
        return 0.0
    elif fecha < FECHA_CAMBIO:
        return minutos * PRECIO_1
    else:
        return minutos * PRECIO_2

def parse_pdf(file):
    registros = []
    try:
        with pdfplumber.open(file) as pdf:
            last_fecha = None
            for page in pdf.pages:
                cols = _find_columns(page)
                words = page.extract_words(x_tolerance=2, y_tolerance=2, use_text_flow=False)
                lines = {}
                for w in words:
                    if w["top"] <= cols["header_bottom"]:
                        continue
                    y_key = round(w["top"], 1)
                    lines.setdefault(y_key, []).append(w)
                for y in sorted(lines.keys()):
                    row_words = sorted(lines[y], key=lambda k: k["x0"])
                    fecha_tokens, hi_tokens, hf_tokens = [], [], []
                    for w in row_words:
                        t = (w.get("text") or "").strip()
                        xmid = (w["x0"] + w["x1"]) / 2.0
                        if _in_range(xmid, cols["fecha"]):
                            fecha_tokens.append(t)
                        elif _in_range(xmid, cols["hi"]):
                            hi_tokens.append(t)
                        elif _in_range(xmid, cols["hf"]):
                            hf_tokens.append(t)
                    fecha_val = " ".join(fecha_tokens).strip()
                    hi_raw = " ".join(hi_tokens).strip()
                    hf_raw = " ".join(hf_tokens).strip()
                    if not fecha_val and last_fecha:
                        fecha_val = last_fecha
                    elif fecha_val:
                        last_fecha = fecha_val
                    hi_list = [_normalize_hour(x) for x in hi_raw.split() if ":" in x and x.count(":") == 1]
                    hf_list = [_normalize_hour(x) for x in hf_raw.split() if ":" in x and x.count(":") == 1]
                    hi_val = hi_list[0] if hi_list else ""
                    hf_val = hf_list[-1] if hf_list else ""
                    minutos = nocturnity_minutes(hi_val, hf_val)
                    dinero = calcular_dinero(fecha_val, minutos)
                    registros.append({
                        "fecha": fecha_val,
                        "hi": hi_val,
                        "hf": hf_val,
                        "nocturnidad_minutos": minutos,
                        "dinero": round(dinero, 2),
                        "linea_completa": " ".join([w["text"] for w in row_words])
                    })
    except Exception as e:
        print(f"[parser] Error al leer PDF {file}:", e)
    return registros

def parse_multiple_pdfs(files):
    all_results = {}
    for f in files:
        print(f"\n[parser] Procesando {f}...")
        all_results[f] = parse_pdf(f)
    return all_results
