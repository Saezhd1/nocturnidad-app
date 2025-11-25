import pdfplumber
import re

def parse_pdf(file):
    registros = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                # Dividir por líneas
                for line in text.splitlines():
                    # Buscar fecha dd/mm/yyyy
                    fecha_m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", line)
                    # Buscar todas las horas HH:MM en la línea
                    horas = re.findall(r"\b([0-2]?\d:[0-5]\d)\b", line)

                    if fecha_m and len(horas) >= 2:
                        fecha = fecha_m.group(1)
                        # Emparejar horas de dos en dos
                        for i in range(0, len(horas)-1, 2):
                            registros.append({
                                "fecha": fecha,
                                "hi": horas[i],
                                "hf": horas[i+1]
                            })
    except Exception as e:
        print("Error al leer PDF:", e)

    print("Registros extraídos:", registros)  # 🔎 debug
    return registros
