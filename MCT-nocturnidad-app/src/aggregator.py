def agregar_resumen(resultados):
    resumen = {}
    for r in resultados:
        fecha = r.get("fecha", "")
        partes = fecha.split("/")
        if len(partes) < 3:
            # Fecha inválida → saltar o marcar como 0
            mes, anio = "0", "0"
        else:
            mes, anio = partes[1], partes[2]

        clave = f"{mes}/{anio}"
        if clave not in resumen:
            resumen[clave] = {"total": 0, "validos": 0}
        resumen[clave]["total"] += 1
        if r["hi"] != 0 and r["hf"] != 0:
            resumen[clave]["validos"] += 1
    return resumen
