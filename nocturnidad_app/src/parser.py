import pdfplumber, re

def parse_pdf(file):
    registros = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                fecha_m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", line)
                horas = re.findall(r"\b([0-2]?\d:[0-5]\d)\b", line)
                if fecha_m and len(horas) >= 2:
                    fecha = fecha_m.group(1)
                    for i in range(0, len(horas)-1, 2):
                        registros.append({
                            "fecha": fecha,
                            "hi": horas[i],
                            "hf": horas[i+1]
                        })
    print("Registros extraídos:", registros)
    return registros

