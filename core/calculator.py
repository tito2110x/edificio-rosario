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

    for dpto_info in DEPARTAMENTOS:
        dpto = dpto_info["dpto"]
        act = float(lecturas_actuales.get(dpto, 0.0))
        ant = float(lecturas_anteriores.get(dpto, 0.0))
        consumo = max(0.0, act - ant) if ant > 0 else 0.0
        consumos[dpto] = consumo
        total_consumo += consumo

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

def calcular_resumen_cobranza(
    calculo_agua: dict,
    monto_luz_comun: float = 0.0,
    cobros_luz_internos: dict[str, float] = None,
    kwh_luz_internos: dict[str, float] = None,
    cuota_mantenimiento: float = 30.0,
    gastos_fijos: dict = None
) -> tuple[list[dict], dict]:
    """
    Calcula exactamente lo que paga cada vecino:
    - 101 al 502: Agua + Cuota Mantenimiento (S/ 30.00).
    - 601 y 602: Agua + Cuota Mantenimiento (S/ 30.00) + Luz propia.
    Nadie paga luz común ni internet por fuera: todo eso se financia con las cuotas de 30.
    
    Retorna:
    - list[dict]: Lista de cobranza para cada vecino (Agua, Cuota, Luz propia si aplica, Total).
    - dict: Balance interno de la administración (Ingresos cuotas vs Luz común, Internet, Limpieza).
    """
    if cobros_luz_internos is None:
        cobros_luz_internos = {}
    if kwh_luz_internos is None:
        kwh_luz_internos = {}
    if gastos_fijos is None:
        gastos_fijos = DEFAULT_GASTOS_COMUNES

    mapa_agua = {d["dpto"]: d for d in calculo_agua["departamentos"]}
    cobranza = []

    for dpto_info in DEPARTAMENTOS:
        dpto = dpto_info["dpto"]
        nombre = dpto_info["nombre"]
        data_agua = mapa_agua.get(dpto, {})
        soles_agua = data_agua.get("total_soles", 0.0)

        # Luz propia solo para 601 y 602
        luz_propia = cobros_luz_internos.get(dpto, 0.0) if dpto in ["601", "602"] else 0.0
        kwh_propia = kwh_luz_internos.get(dpto, 0.0) if dpto in ["601", "602"] else 0.0

        # Total a pagar por este vecino
        total_a_pagar = round(soles_agua + cuota_mantenimiento + luz_propia, 2)

        cobranza.append({
            "dpto": dpto,
            "nombre": nombre,
            "agua_soles": soles_agua,
            "cuota_mantenimiento": cuota_mantenimiento,
            "luz_propia": luz_propia,
            "kwh_propia": kwh_propia,
            "total_a_pagar": total_a_pagar,
            "consumo_m3": data_agua.get("consumo", 0.0),
            "lectura_anterior_agua": data_agua.get("lectura_anterior", 0.0),
            "lectura_actual_agua": data_agua.get("lectura_actual", 0.0),
            "alerta_fuga": data_agua.get("alerta_fuga", False)
        })

    # Balance interno de administración del edificio
    num_dptos = len(DEPARTAMENTOS)
    total_ingresos_cuotas = round(num_dptos * cuota_mantenimiento, 2)
    internet_costo = gastos_fijos.get("internet", 150.0)
    limpieza_costo = gastos_fijos.get("limpieza", 100.0)
    total_egresos_comunes = round(monto_luz_comun + internet_costo + limpieza_costo, 2)
    saldo_mes = round(total_ingresos_cuotas - total_egresos_comunes, 2)

    balance_admin = {
        "num_dptos": num_dptos,
        "cuota_unitaria": cuota_mantenimiento,
        "total_ingresos_cuotas": total_ingresos_cuotas,
        "egreso_luz_comun": monto_luz_comun,
        "egreso_internet": internet_costo,
        "egreso_limpieza": limpieza_costo,
        "total_egresos": total_egresos_comunes,
        "saldo_mes": saldo_mes
    }

    return cobranza, balance_admin

# Alias de compatibilidad
def calcular_resumen_general(*args, **kwargs):
    cobranza, _ = calcular_resumen_cobranza(*args, **kwargs)
    return cobranza
