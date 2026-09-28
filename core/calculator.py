from config import DEPARTAMENTOS, DEFAULT_GASTOS_COMUNES

def calcular_prorrateo_agua(
    lecturas_actuales: dict[str, float],
    lecturas_anteriores: dict[str, float],
    monto_recibo_sedapal: float,
    totales_mes_anterior: dict[str, float] = None
) -> dict:
    """
    Calcula el consumo de cada departamento y prorratea el recibo de Sedapal
    de forma idéntica a la hoja AGUA de Consumo agua edificio.xlsx.
    """
    if totales_mes_anterior is None:
        totales_mes_anterior = {}

    consumos = {}
    total_consumo = 0.0

    # 1. Calcular consumo por departamento
    for dpto_info in DEPARTAMENTOS:
        dpto = dpto_info["dpto"]
        act = float(lecturas_actuales.get(dpto, 0.0))
        ant = float(lecturas_anteriores.get(dpto, 0.0))
        consumo = max(0.0, act - ant) if ant > 0 else 0.0
        consumos[dpto] = consumo
        total_consumo += consumo

    # 2. Prorratear monto en soles
    resultados = []
    total_soles_calculado = 0.0

    for dpto_info in DEPARTAMENTOS:
        dpto = dpto_info["dpto"]
        nombre = dpto_info["nombre"]
        act = float(lecturas_actuales.get(dpto, 0.0))
        ant = float(lecturas_anteriores.get(dpto, 0.0))
        consumo = consumos[dpto]

        porcentaje = (consumo / total_consumo) if total_consumo > 0 else 0.0
        total_soles = porcentaje * monto_recibo_sedapal
        total_soles_calculado += total_soles

        anterior_soles = totales_mes_anterior.get(dpto, 0.0)
        variacion_pct = ((total_soles / anterior_soles) - 1.0) if anterior_soles > 0 else 0.0

        # Alerta de posible fuga: si el consumo creció más del 60% respecto al mes anterior
        alerta_fuga = False
        if anterior_soles > 0 and variacion_pct > 0.60:
            alerta_fuga = True

        resultados.append({
            "dpto": dpto,
            "nombre": nombre,
            "lectura_anterior": ant,
            "lectura_actual": act,
            "consumo": consumo,
            "porcentaje": porcentaje,
            "total_soles": round(total_soles, 2),
            "anterior_soles": round(anterior_soles, 2),
            "variacion_pct": variacion_pct,
            "alerta_fuga": alerta_fuga
        })

    return {
        "monto_recibo": monto_recibo_sedapal,
        "total_consumo": total_consumo,
        "total_soles_prorrateado": round(total_soles_calculado, 2),
        "departamentos": resultados
    }

def calcular_resumen_general(
    calculo_agua: dict,
    monto_luz_comun: float = 0.0,
    gastos_fijos: dict = None,
    cobros_luz_internos: dict[str, float] = None
) -> list[dict]:
    """
    Integra la pestaña RESUMEN de Consumo agua edificio.xlsx:
    Agua + Cuota Mantenimiento + Gastos comunes (Luz, Internet, Limpieza).
    """
    if gastos_fijos is None:
        gastos_fijos = DEFAULT_GASTOS_COMUNES
    if cobros_luz_internos is None:
        cobros_luz_internos = {}

    num_dptos = len(DEPARTAMENTOS)
    cuota = gastos_fijos.get("cuota_mantenimiento", 30.0)
    internet_total = gastos_fijos.get("internet", 150.0)
    limpieza_total = gastos_fijos.get("limpieza", 100.0)

    luz_por_dpto = round(monto_luz_comun / num_dptos, 2)
    internet_por_dpto = round(internet_total / num_dptos, 2)
    limpieza_por_dpto = round(limpieza_total / num_dptos, 2)
    total_comunes_dpto = round(luz_por_dpto + internet_por_dpto + limpieza_por_dpto, 2)
    saldo_cuota = round(cuota - total_comunes_dpto, 2)

    resumen = []
    mapa_agua = {d["dpto"]: d for d in calculo_agua["departamentos"]}

    for dpto_info in DEPARTAMENTOS:
        dpto = dpto_info["dpto"]
        nombre = dpto_info["nombre"]
        data_agua = mapa_agua.get(dpto, {})
        soles_agua = data_agua.get("total_soles", 0.0)

        # Luz propia interna si aplica (ej. dptos 601 o 602)
        luz_propia = cobros_luz_internos.get(dpto, 0.0)

        total_a_pagar = round(soles_agua + cuota + luz_propia, 2)

        resumen.append({
            "dpto": dpto,
            "nombre": nombre,
            "agua_soles": soles_agua,
            "cuota_mantenimiento": cuota,
            "luz_propia": luz_propia,
            "luz_comun": luz_por_dpto,
            "internet": internet_por_dpto,
            "limpieza": limpieza_por_dpto,
            "total_areas_comunes": total_comunes_dpto,
            "saldo_fondo": saldo_cuota,
            "total_a_pagar": total_a_pagar,
            "alerta_fuga": data_agua.get("alerta_fuga", False),
            "consumo": data_agua.get("consumo", 0.0),
            "lectura_anterior": data_agua.get("lectura_anterior", 0.0),
            "lectura_actual": data_agua.get("lectura_actual", 0.0)
        })

    return resumen
