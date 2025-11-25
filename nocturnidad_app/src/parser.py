import pdfplumber

def _find_header_columns(page):
    """
    Encuentra las posiciones X aproximadas de las columnas 'Fecha', 'HI' y 'HF'
    buscando las palabras de cabecera en la página.
    Devuelve dict con rangos x: {'fecha': (x0,x1), 'hi': (x0,x1), 'hf': (x0,x1), 'header_bottom': y}
    """
    words = page.extract_words(use_text_flow=True)
    fecha_x = hi_x = hf_x = None
    header_bottom = None

    for w in words:
        txt = (w.get("text") or "").strip().lower()
        if txt == "fecha":
            fecha_x = (w["x0"], w["x1"])
            header_bottom = w["bottom"]
        elif txt == "hi":
            hi_x = (w["x0"], w["x1"])
            header_bottom = max(header_bottom or 0, w["bottom"])
        elif txt == "hf":
            hf_x = (w["x0"], w["x1"])
            header_bottom = max(header_bottom or 0, w["bottom"])

    # Si no encuentra cabeceras, fallback a rangos aproximados (últimas columnas para HI/HF)
    if not (fecha_x and hi_x and hf_x):
        # Heurística: dividir el ancho en bandas, situando HI/HF en el último tercio
        x0_page, x1_page = page.bbox[0], page.bbox[2]
        width = x1_page - x0_page
        fecha_x = (x0_page + 0.05 * width, x0_page + 0.20 * width)
        hi_x    = (x0_page + 0.70 * width, x0_page + 0.82 * width)
        hf_x    = (x0_page + 0.82 * width, x0_page + 0.95 * width)
        header_bottom = header_bottom or (page.bbox[1] + 40)

    return {
        "fecha": fecha_x,
        "hi": hi_x,
        "hf": hf_x,
        "header_bottom": header_bottom
    }

def _in_range(xmid, xr):
    return xr[0] - 2 <= xmid <= xr[1] + 2  # pequeña tolerancia

def parse_pdf(file):
    registros = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                cols = _find_header_columns(page)
                words = page.extract_words(x_tolerance=2, y_tolerance=2, use_text_flow=False)
                # Agrupar por "línea" usando la coordenada top redondeada
                lines = {}
                for w in words:
                    if w["top"] <= cols["header_bottom"]:
                        continue  # ignorar cabeceras
                    key = round(w["top"], 1)
                    lines.setdefault(key, []).append(w)

                # Ordenar líneas por posición vertical
                for y in sorted(lines.keys()):
                    ws = sorted(lines[y], key=lambda k: k["x0"])
                    fecha_txt, hi_txt, hf_txt = [], [], []

                    for w in ws:
                        xmid = (w["x0"] + w["x1"]) / 2.0
                        t = (w.get("text") or "").strip()
                        if _in_range(xmid, cols["fecha"]):
                            fecha_txt.append(t)
                        elif _in_range(xmid, cols["hi"]):
                            hi_txt.append(t)
                        elif _in_range(xmid, cols["hf"]):
                            hf_txt.append(t)
                        else:
                            # fuera de rango; ignorar
                            pass

                    fecha_val = " ".join(fecha_txt).strip()
                    hi_val = " ".join(hi_txt).strip()
                    hf_val = " ".join(hf_txt).strip()

                    # Herencia de fecha para líneas partidas
                    if not fecha_val and registros:
                        fecha_val = registros[-1]["fecha"]

                    # Filtrar líneas que no tengan horas en ninguna de las dos columnas
                    if not (hi_val or hf_val):
                        continue

                    # Normalizar separadores: múltiple horarios por espacio
                    hi_list = [h for h in hi_val.split() if ":" in h]
                    hf_list = [h for h in hf_val.split() if ":" in h]

                    # Emparejar por índice
                    for i in range(min(len(hi_list), len(hf_list))):
                        registros.append({
                            "fecha": fecha_val,
                            "hi": hi_list[i],
                            "hf": hf_list[i]
                        })
    except Exception as e:
        print("Error al leer PDF:", e)

    print(f"[parser] Registros extraídos: {len(registros)}")
    # Debug opcional: mostrar primeros
    for r in registros[:6]:
        print("[parser] Ej:", r)
    return registros
