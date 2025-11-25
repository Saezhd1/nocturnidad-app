import pdfplumber

def parse_pdf(file):
    registros = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue

                header = table[0]
                try:
                    idx_hi = header.index("HI")
                    idx_hf = header.index("HF")
                except ValueError:
                    idx_hi, idx_hf = 15, 16  # fallback

                for row in table[1:]:
                    fecha = row[0]
                    hi = row[idx_hi] if len(row) > idx_hi else None
                    hf = row[idx_hf] if len(row) > idx_hf else None

                    # Normalizar formato de hora
                    if hi and "." in hi:
                        hi = hi.replace(".", ":")[:5]
                    if hf and "." in hf:
                        hf = hf.replace(".", ":")[:5]

                    if hi and hf:
                        registros.append({"fecha": fecha, "hi": hi, "hf": hf})
    except Exception as e:
        print("Error al leer PDF:", e)

    print("Registros extraídos:", registros)  # 🔎 debug
    return registros
