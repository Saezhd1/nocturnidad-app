from datetime import datetime, timedelta

NOCTURNIDAD_INICIO = 22  # 22:00
NOCTURNIDAD_FIN = 6      # 06:00
VALOR_MINUTO = 0.5       # ejemplo: 0.5 €/minuto

def calcular_nocturnidad_global(registros):
    detalle = []
    total_minutos = 0
    total_importe = 0.0

    for r in registros:
        try:
            hi = datetime.strptime(r["hi"], "%H:%M")
            hf = datetime.strptime(r["hf"], "%H:%M")
        except Exception as e:
            print("[nocturnidad] error parseando hora:", r, e)
            continue

        # Si la hora final es menor o igual que la inicial, cruza medianoche
        if hf <= hi:
            hf += timedelta(days=1)

        minutos_nocturnos = 0
        actual = hi
        while actual < hf:
            h = actual.hour
            if h >= NOCTURNIDAD_INICIO or h < NOCTURNIDAD_FIN:
                minutos_nocturnos += 1
            actual += timedelta(minutes=1)

        importe = minutos_nocturnos * VALOR_MINUTO

        detalle.append({
            "fecha": r["fecha"],
            "hi": r["hi"],
            "hf": r["hf"],
            "minutos": minutos_nocturnos,
            "importe": round(importe, 2)
        })

        total_minutos += minutos_nocturnos
        total_importe += importe

        # 🔎 Log detallado por tramo
        print(f"[nocturnidad] {r['fecha']} {r['hi']}-{r['hf']} -> {minutos_nocturnos} min, {round(importe,2)} €")

    # 🔎 Log resumen global
    print(f"[nocturnidad] Total: {total_minutos} min, {round(total_importe,2)} €")

    return {
        "detalle": detalle,
        "total_minutos": total_minutos,
        "total_importe": round(total_importe, 2)
    }
