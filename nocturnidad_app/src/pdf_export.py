from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.units import cm
from io import BytesIO
from PyPDF2 import PdfReader

def _tabla_dias(resultados_por_pdf):
    rows = [["Archivo", "Fecha", "Minutos nocturnos", "Importe (€)"]]
    for doc in resultados_por_pdf:
        fn = doc['filename']
        for d in doc['dias']:
            if d['minutos_nocturnos'] > 0:
                rows.append([fn, d['fecha'], str(d['minutos_nocturnos']), d['importe']])
    return rows

def _tabla_mes(resumen):
    rows = [["Mes/Año", "Minutos", "Importe (€)", "Días"]]
    for k, v in sorted(resumen['por_mes'].items()):
        rows.append([k, str(v['minutos']), f"{v['importe']:.2f}", str(v['dias'])])
    return rows

def _tabla_global(resumen):
    t = resumen['global']
    return [["Total minutos", "Total importe (€)", "Total días"],
            [str(t['minutos']), f"{t['importe']:.2f}", str(t['dias'])]]

def contar_paginas(story):
    temp_buffer = BytesIO()
    temp_doc = SimpleDocTemplate(temp_buffer, pagesize=A4)
    temp_doc.build(story)
    temp_buffer.seek(0)
    reader = PdfReader(temp_buffer)
    return len(reader.pages)

def pie_de_pagina(total_pages):
    def inner(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"{page_num} de {total_pages}"
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(36, 20, "(MCT) Movimiento Social Laboral de Conductores de TITSA")
        canvas.drawRightString(550, 20, text)
        canvas.restoreState()
    return inner

def exportar_pdf_informe(empleado, nombre, resultados, resumen):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Logo + encabezado
    logo = Image("static/mct_logo.png", width=2.5*cm, height=2.5*cm)
    story += [logo, Spacer(1, 6)]
    story += [Paragraph("MCT", styles['Title']), Spacer(1, 6)]
    story += [Paragraph("Informe tramos de nocturnidad del servicio realizado", styles['Heading1']), Spacer(1, 24)]

    # Identificación
    ident = Paragraph(f"Número de empleado: {empleado} &nbsp;&nbsp;|&nbsp;&nbsp; Nombre: {nombre}", styles['Normal'])
    story += [ident, Spacer(1, 24)]

    # Tabla por días
    dias_tbl = Table(_tabla_dias(resultados))
    dias_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eeeeee')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
        ('ALIGN', (2,1), (3,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    story += [Paragraph("Detalle por día (solo días con nocturnidad)", styles['Heading2']), Spacer(1, 6), dias_tbl, Spacer(1, 18)]

    # Tabla por mes
    mes_tbl = Table(_tabla_mes(resumen))
    mes_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eeeeee')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    story += [Paragraph("Resumen mensual", styles['Heading2']), Spacer(1, 6), mes_tbl, Spacer(1, 18)]

    # Tabla global
    global_tbl = Table(_tabla_global(resumen))
    global_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eeeeee')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
        ('ALIGN', (0,1), (-1,1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    story += [Paragraph("Resumen global", styles['Heading2']), Spacer(1, 6), global_tbl, Spacer(1, 24)]

    # Explicación final
    explicacion = """
    Este informe calcula los minutos de nocturnidad según los tramos definidos en el ACTA acuerdo de nocturnidad emitido por:<br/>
    <b>JUZGADO DE LO SOCIAL Nº4 de S/C de Tenerife</b><br/>
    <b>Procedimiento:</b> Ejecución de títulos judiciales<br/>
    <b>Nº Procedimiento:</b> 0000055/2025<br/><br/>
    <b>Importe por minuto:</b><br/>
    - Desde el 30/03/2022 Hasta el 25/04/2025: 0,05 € (1h = 3 €)<br/>
    - Desde el 26/04/2025: 0,062 € (1h = 3,72 €)<br/><br/>
    <b>Tramos nocturnos considerados:</b><br/>
    - 22:00 a 00:59<br/>
    - 04:00 a 06:00
    """
    story += [Paragraph(explicacion, styles['Normal'])]

    # Calcular total de páginas
    total_pages = contar_paginas(story)

    # Construir documento con pie de página
    doc.build(story, onFirstPage=pie_de_pagina(total_pages), onLaterPages=pie_de_pagina(total_pages))
    return buffer
