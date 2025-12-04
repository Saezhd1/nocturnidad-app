import pdfplumber
import os

def _in_range(xmid, xr, tol=2):
    return xr[0] - tol <= xmid <= xr[1] + tol

def _find_columns(page):
    """
    Encuentra rangos X para columnas clave. Prioriza cabeceras reales; si falla, usa rangos fijos
    ajustados a este modelo de TITSA.
    """
    words = page.extract_words(use_text_flow=True)
    fecha_x = hi_x = hf_x = None
    header_bottom = page.bbox[1] + 40  # altura aproximada bajo cabecera

    for w in words:
        t = (w.get("text") or "").strip().lower()
        if t == "fecha":
            fecha_x = (w["x0"], w["x1"]); header_bottom = max(header_bottom, w["bottom"])
        elif t == "hi":
            hi_x = (w["x0"], w["x1"]); header_bottom = max(header_bottom, w["bottom"])
        elif t == "hf":
            hf_x = (w["x0"], w["x1"]); header_bottom = max(header_bottom, w["bottom"])

    # Fallback “hardcodeado” para este modelo si no encuentra cabeceras
    if not (fecha_x and hi_x and hf_x):
        x0_page, x1_page = page.bbox[0], page.bbox[2]
        width = x1_page - x0_page
        fecha_x = (x0_page + 0.06 * width, x0_page + 0.22 * width)
        hi_x    = (x0_page + 0.69 * width, x0_page + 0.81 * width)
        hf_x    = (x0_page + 0.81 * width, x0_page + 0.95 * width)

    print(f"[parser] Columnas detectadas -> fecha:{fecha_x}, hi:{hi_x}, hf:{hf_x}")
    return {"fecha": fecha_x, "hi": hi_x, "hf": hf_x, "header_bottom": header_bottom}

def parse_pdf(file):
    registros = []
    current_fecha = None
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                cols = _find_columns(page)
                # Palabras con tolerancias pequeñas para que se agrupen por línea
                words = page.extract_words(x_tolerance=3, y_tolerance=3, use_text_flow=False)
                
                # Agrupar por línea (clave: y redondeada)
                lines = {}
                for w in words:
                    if w["top"] <= cols["header_bottom"]:
                        continue
                    y_key = round(w["top"], 1)
                    lines.setdefault(y_key, []).append(w)

                # Ordenar por vertical
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

                    # Consolidar
                    fecha_val = " ".join(fecha_tokens).strip()
                    hi_raw = " ".join(hi_tokens).strip()
                    hf_raw = " ".join(hf_tokens).strip()

                    # Si aparece una nueva fecha, actualiza el marcador
                    if fecha_val:
                        current_fecha = fecha_val
                        continue  # no asociar horas en la misma línea que la fecha
                    
                    # Si hay horas y ya tenemos una fecha activa, asociarlas a esa fecha
                    if current_fecha and (hi_raw or hf_raw):
                        hi_list = [x for x in hi_raw.split() if ":" in x and x.count(":") == 1]
                        hf_list = [x for x in hf_raw.split() if ":" in x and x.count(":") == 1]

                        # Asociar todas las combinaciones de HI y HF
                        for hi in hi_list:
                            for hf in hf_list:
                                registros.append({
                                    "fecha": current_fecha,
                                    "hi": hi,
                                    "hf": hf,
                                    "principal": True
                                })

        print(f"[parser] Total registros extraídos: {len(registros)}")
    except Exception as e:
        print("[parser] Error al leer PDF:", e)
    return registros
    
# 🔑 NUEVO: función para varios PDFs
def parse_multiple_pdfs(files):
    """
    files: lista de rutas de archivos PDF
    Devuelve un diccionario con resultados por archivo
    """
    resultados = {}
    for f in files:
        print(f"[parser] Procesando: {os.path.basename(f)}")
        registros = parse_pdf(f)
        # Añadir origen al registro
    for r in registros:
        r["archivo"] = os.path.basename(f)
        resultados[f] = registros
        print(f"[parser] {len(registros)} registros extraídos de {os.path.basename(f)}")
    return resultados
    
    print(f"[parser] Registros extraídos: {len(registros)}")
    for r in registros[:6]:
        print("[parser] Ej:", r)
    return registros







