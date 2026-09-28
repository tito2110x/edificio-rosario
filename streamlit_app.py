import streamlit as st
import traceback
import sys
import os

# Configuración de página como primer comando de Streamlit
st.set_page_config(
    page_title="Rosario del Solar - Cobranza Mensual",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

try:
    import pandas as pd
    from datetime import datetime

    from config import (
        obtener_gemini_api_key, PRIMARY_MODEL,
        DEPARTAMENTOS, DEFAULT_GASTOS_COMUNES
    )
    from core.gemini_reader import procesar_lote_fotos
    from core.receipt_reader import analizar_recibo_luz, analizar_recibo_agua
    from core.calculator import calcular_prorrateo_agua, calcular_resumen_cobranza
    from core.database import obtener_lecturas_base, guardar_mes

    # Estilos CSS Mobile-First y de alta legibilidad
    st.markdown("""
    <style>
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
        }
        .main-header {
            background: linear-gradient(135deg, #0D47A1 0%, #1976D2 100%);
            color: white;
            padding: 20px 22px;
            border-radius: 12px;
            margin-bottom: 22px;
            box-shadow: 0 4px 12px rgba(13, 71, 161, 0.15);
        }
        .main-header h1 {
            color: white !important;
            font-size: 1.75rem;
            margin: 0;
            font-weight: 700;
        }
        .main-header p {
            color: #E3F2FD !important;
            margin: 6px 0 0 0;
            font-size: 0.95rem;
        }
        .badge-total {
            background-color: #E8F5E9;
            color: #1B5E20;
            padding: 8px 14px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.18rem;
            text-align: center;
            border: 1px solid #C8E6C9;
        }
        .metric-card {
            background: #F8FAFC;
            padding: 14px 18px;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
        }
        .info-pill {
            display: inline-block;
            background: #EFF6FF;
            color: #1D4ED8;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    # Encabezado Principal
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Edificio Rosario del Solar</h1>
        <p>Sistema mensual de Agua, Luz y Fondo de Mantenimiento</p>
    </div>
    """, unsafe_allow_html=True)

    # Cargar historial base (Agosto 2026)
    nombre_mes_ant, lecturas_agua_ant, lecturas_luz_ant = obtener_lecturas_base()

    # Barra lateral discreta sin nada de API Keys ni tecnicismos
    with st.sidebar:
        st.markdown("### 🏢 Edificio Rosario del Solar")
        st.caption("12 Departamentos • Administración")
        st.info(f"📅 **Mes Anterior Registrado:**\n\n**{nombre_mes_ant}**")
        st.markdown("---")
        st.markdown("""
        **Guía Rápida para el Mes:**
        1. 📄 **Paso 1:** Sube las fotos de los recibos de Sedapal y Luz del Sur.
        2. 📸 **Paso 2:** Sube las fotos de los medidores.
        3. 💰 **Paso 3:** Revisa los montos a cobrar a cada vecino y copia los mensajes a WhatsApp.
        4. 📊 **Paso 4:** Revisa el balance interno de la caja de mantenimiento.
        5. 💾 **Paso 5:** Guarda el mes para cerrar el ciclo.
        """)

    # Inicializar Session State
    if "recibo_agua_monto" not in st.session_state:
        st.session_state.recibo_agua_monto = 0.0
    if "recibo_luz_monto" not in st.session_state:
        st.session_state.recibo_luz_monto = 0.0
    if "recibo_luz_kwh" not in st.session_state:
        st.session_state.recibo_luz_kwh = 0.0

    if "lecturas_agua_detectadas" not in st.session_state:
        st.session_state.lecturas_agua_detectadas = lecturas_agua_ant.copy()
    if "lecturas_luz_detectadas" not in st.session_state:
        st.session_state.lecturas_luz_detectadas = lecturas_luz_ant.copy()
    if "costo_internet" not in st.session_state:
        st.session_state.costo_internet = 150.0
    if "costo_limpieza" not in st.session_state:
        st.session_state.costo_limpieza = 100.0

    # -------------------------------------------------------------
    # PASO 1: SUBIR RECIBOS (FOTOS)
    # -------------------------------------------------------------
    st.subheader("1. 📄 Recibos del Mes (Sedapal y Luz del Sur)")
    st.caption("Sube las fotos o ingresa los montos directamente.")

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("##### 💧 Recibo de Agua (Sedapal)")
        foto_recibo_agua = st.file_uploader(
            "Foto del Recibo de Sedapal",
            type=["jpg", "jpeg", "png", "pdf"],
            key="uploader_recibo_agua"
        )
        if foto_recibo_agua:
            if st.button("🤖 Leer Recibo de Agua con IA", key="btn_leer_agua", use_container_width=True):
                with st.spinner("Leyendo recibo de Sedapal..."):
                    m_type = foto_recibo_agua.type or "image/jpeg"
                    res_a = analizar_recibo_agua(foto_recibo_agua.getvalue(), mime_type=m_type)
                    if res_a.get("total_a_pagar", 0) > 0:
                        st.session_state.recibo_agua_monto = res_a["total_a_pagar"]
                        st.success(f"✅ Sedapal detectado: S/ {res_a['total_a_pagar']:.2f}")
                    else:
                        st.warning("No se pudo detectar el monto automáticamente. Ingrésalo manualmente abajo.")

    with col_r2:
        st.markdown("##### ⚡ Recibo de Luz (Luz del Sur)")
        foto_recibo_luz = st.file_uploader(
            "Foto del Recibo de Luz del Sur",
            type=["jpg", "jpeg", "png", "pdf"],
            key="uploader_recibo_luz"
        )
        if foto_recibo_luz:
            if st.button("🤖 Leer Recibo de Luz con IA", key="btn_leer_luz", use_container_width=True):
                with st.spinner("Leyendo recibo de Luz del Sur..."):
                    m_type = foto_recibo_luz.type or "image/jpeg"
                    res_l = analizar_recibo_luz(foto_recibo_luz.getvalue(), mime_type=m_type)
                    if res_l.get("total_a_pagar", 0) > 0:
                        st.session_state.recibo_luz_monto = res_l["total_a_pagar"]
                        st.session_state.recibo_luz_kwh = res_l["energia_facturada_kwh"]
                        st.success(f"✅ Luz detectada: S/ {res_l['total_a_pagar']:.2f} ({res_l['energia_facturada_kwh']:.1f} kWh)")
                    else:
                        st.warning("No se pudo detectar el monto automáticamente. Ingrésalo manualmente abajo.")

    # Entradas numéricas de recibos
    st.markdown("**Valores de los Recibos de este mes:**")
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        monto_agua_input = st.number_input(
            "💧 Sedapal Total a Pagar (S/.)",
            value=float(st.session_state.recibo_agua_monto),
            step=10.0,
            format="%.2f",
            help="Este monto se prorratea entre todos los 12 departamentos según el consumo de agua."
        )
    with c_m2:
        monto_luz_input = st.number_input(
            "⚡ Luz del Sur Total (S/.)",
            value=float(st.session_state.recibo_luz_monto),
            step=10.0,
            format="%.2f",
            help="Solo se usa para costear el kWh de los medidores de los dptos 601 y 602, y la luz común."
        )
    with c_m3:
        kwh_luz_input = st.number_input(
            "⚡ Luz del Sur Energía (kWh)",
            value=float(st.session_state.recibo_luz_kwh),
            step=5.0,
            format="%.2f",
            help="Total de kWh facturados en el recibo general de Luz del Sur."
        )

    st.divider()

    # -------------------------------------------------------------
    # PASO 2: SUBIR FOTOS DE LOS MEDIDORES
    # -------------------------------------------------------------
    st.subheader("2. 📸 Fotos de los Medidores")
    st.caption(f"Sube las fotos de los contadores. Las lecturas anteriores se comparan contra **{nombre_mes_ant}**.")

    fotos_medidores_files = st.file_uploader(
        "Selecciona todas las fotos de los medidores juntas desde tu galería o cámara:",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="uploader_medidores_masivo"
    )

    if fotos_medidores_files:
        st.info(f"📁 {len(fotos_medidores_files)} fotos seleccionadas listas para analizar.")
        if st.button("🚀 Escanear Medidores con IA", type="primary", use_container_width=True):
            f_dict = {f.name: f.getvalue() for f in fotos_medidores_files}
            with st.spinner("Analizando stickers de dpto y lecturas con IA..."):
                res_lote = procesar_lote_fotos(f_dict)
                actualizados = []
                for name, r in res_lote.items():
                    dpto = r.get("departamento")
                    tipo = r.get("tipo", "agua")
                    lectura = float(r.get("lectura_entera", 0))
                    if dpto:
                        if dpto in ["601", "602"] and tipo == "luz":
                            st.session_state.lecturas_luz_detectadas[dpto] = float(r.get("lectura_decimal", lectura))
                            actualizados.append(f"Luz {dpto}")
                        else:
                            st.session_state.lecturas_agua_detectadas[dpto] = lectura
                            actualizados.append(f"Agua {dpto}")

                if actualizados:
                    st.success(f"✅ Se detectaron con éxito: {', '.join(actualizados)}")
                else:
                    st.warning("No se pudieron identificar las etiquetas en las fotos. Puedes ingresar los números manualmente abajo.")

    # Panel expandible para revisar o corregir lecturas
    with st.expander("✏️ Ver / Ajustar Lecturas Actuales de los Medidores (Clic aquí)", expanded=False):
        st.markdown("#### 💧 Medidores de Agua (12 Departamentos)")
        cols_agua = st.columns(3)
        for idx, dpto_info in enumerate(DEPARTAMENTOS):
            dpto = dpto_info["dpto"]
            col_target = cols_agua[idx % 3]
            with col_target:
                ant_val = lecturas_agua_ant.get(dpto, 0.0)
                cur_val = float(st.session_state.lecturas_agua_detectadas.get(dpto, ant_val))
                nueva_lect = st.number_input(
                    f"Dpto {dpto} (Ant: {ant_val:,.0f})",
                    value=cur_val,
                    step=100.0,
                    format="%.0f",
                    key=f"input_agua_{dpto}"
                )
                st.session_state.lecturas_agua_detectadas[dpto] = nueva_lect

        st.markdown("#### ⚡ Medidores de Luz Internos (Solo 601 y 602)")
        st.caption("ℹ️ *Los demás departamentos pagan su propia luz independiente; solo 601 y 602 tienen medidores internos vinculados al recibo general.*")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            ant_luz_601 = lecturas_luz_ant.get("601", 0.0)
            cur_luz_601 = float(st.session_state.lecturas_luz_detectadas.get("601", ant_luz_601))
            nueva_luz_601 = st.number_input(
                f"Luz Dpto 601 (Ant: {ant_luz_601:,.1f} kWh)",
                value=cur_luz_601,
                step=1.0,
                format="%.1f",
                key="input_luz_601"
            )
            st.session_state.lecturas_luz_detectadas["601"] = nueva_luz_601

        with col_l2:
            ant_luz_602 = lecturas_luz_ant.get("602", 0.0)
            cur_luz_602 = float(st.session_state.lecturas_luz_detectadas.get("602", ant_luz_602))
            nueva_luz_602 = st.number_input(
                f"Luz Dpto 602 (Ant: {ant_luz_602:,.1f} kWh)",
                value=cur_luz_602,
                step=1.0,
                format="%.1f",
                key="input_luz_602"
            )
            st.session_state.lecturas_luz_detectadas["602"] = nueva_luz_602

    st.divider()

    # -------------------------------------------------------------
    # PASO 3: CÁLCULOS Y RESULTADOS
    # -------------------------------------------------------------
    # 1. Prorrateo de Luz
    kwh_601 = max(0.0, float(st.session_state.lecturas_luz_detectadas.get("601", 0.0)) - float(lecturas_luz_ant.get("601", 0.0)))
    kwh_602 = max(0.0, float(st.session_state.lecturas_luz_detectadas.get("602", 0.0)) - float(lecturas_luz_ant.get("602", 0.0)))
    kwh_comun = max(0.0, kwh_luz_input - kwh_601 - kwh_602)

    costo_kwh_promedio = (monto_luz_input / kwh_luz_input) if kwh_luz_input > 0 else 0.0
    soles_luz_601 = round(kwh_601 * costo_kwh_promedio, 2)
    soles_luz_602 = round(kwh_602 * costo_kwh_promedio, 2)
    soles_luz_comun = round(max(0.0, monto_luz_input - soles_luz_601 - soles_luz_602), 2)

    cobros_luz = {"601": soles_luz_601, "602": soles_luz_602}
    kwh_luz = {"601": kwh_601, "602": kwh_602}

    # 2. Prorrateo de Agua
    calculo_agua = calcular_prorrateo_agua(
        lecturas_actuales=st.session_state.lecturas_agua_detectadas,
        lecturas_anteriores=lecturas_agua_ant,
        monto_recibo_sedapal=monto_agua_input
    )

    # 3. Resumen de cobranza y balance de caja
    gastos_fijos_dict = {
        "internet": st.session_state.costo_internet,
        "limpieza": st.session_state.costo_limpieza
    }

    cobranza_vecinos, balance_admin = calcular_resumen_cobranza(
        calculo_agua=calculo_agua,
        monto_luz_comun=soles_luz_comun,
        cobros_luz_internos=cobros_luz,
        kwh_luz_internos=kwh_luz,
        cuota_mantenimiento=30.0,
        gastos_fijos=gastos_fijos_dict
    )

    st.subheader("3. 💰 Resultados y Resumen del Mes")

    tab_vecinos, tab_admin = st.tabs([
        "📱 Cobranza a Vecinos (Mensajes WhatsApp)",
        "🏢 Balance de Administración (Fondo de Mantenimiento)"
    ])

    # PESTAÑA 1: COBRANZA A VECINOS
    with tab_vecinos:
        st.markdown("""
        > **Regla de Cobranza:**
        > - **Dptos 101 al 502:** Pagan su consumo de **Agua** + **Cuota de Mantenimiento (S/ 30.00)**.
        > - **Dptos 601 y 602:** Pagan su consumo de **Agua** + **Luz Propia** + **Cuota de Mantenimiento (S/ 30.00)**.
        > - *(Ningún vecino paga luz común, internet ni limpieza por fuera; todo eso lo asume el fondo de mantenimiento)*.
        """)

        # Tarjetas individuales para cada departamento
        for item in cobranza_vecinos:
            dpto = item["dpto"]
            nombre = item["nombre"]
            agua_s = item["agua_soles"]
            cuota = item["cuota_mantenimiento"]
            luz_prop = item["luz_propia"]
            kwh_prop = item["kwh_propia"]
            tot = item["total_a_pagar"]
            cons_m3 = item["consumo_m3"]
            act_m3 = item["lectura_actual_agua"]

            tiene_luz = (dpto in ["601", "602"] and luz_prop > 0)

            # Texto para WhatsApp personalizado
            if tiene_luz:
                linea_luz = f"\n⚡ Luz Propia ({kwh_prop:.1f} kWh): S/ {luz_prop:.2f}"
            else:
                linea_luz = ""

            msg_whatsapp = (
                f"Hola {nombre} (Dpto {dpto}), te compartimos el detalle de cobranza del mes:\n\n"
                f"💧 Agua ({cons_m3:,.0f} m³): S/ {agua_s:.2f}"
                f"{linea_luz}\n"
                f"🏢 Cuota Mantenimiento: S/ {cuota:.2f}\n"
                f"---------------------------------\n"
                f"👉 TOTAL A PAGAR: S/ {tot:.2f}\n\n"
                f"Muchas gracias por tu puntualidad."
            )

            with st.container(border=True):
                col_c1, col_c2 = st.columns([3, 1])
                with col_c1:
                    st.markdown(f"### Dpto {dpto} — {nombre}")
                    st.write(f"💧 **Agua:** S/ {agua_s:.2f} *(Consumo: {cons_m3:,.0f} m³ | Contador: {act_m3:,.0f})*")
                    if tiene_luz:
                        st.write(f"⚡ **Luz Propia:** S/ {luz_prop:.2f} *(Consumo: {kwh_prop:.1f} kWh)*")
                    st.write(f"🏢 **Cuota Mantenimiento:** S/ {cuota:.2f}")

                with col_c2:
                    st.markdown(f"<div class='badge-total'>Total: S/ {tot:.2f}</div>", unsafe_allow_html=True)
                    st.write("")
                    st.text_area(
                        "Mensaje WhatsApp",
                        value=msg_whatsapp,
                        height=75,
                        key=f"txt_wa_{dpto}",
                        label_visibility="collapsed"
                    )

    # PESTAÑA 2: BALANCE DE ADMINISTRACIÓN (FONDO DE MANTENIMIENTO)
    with tab_admin:
        st.markdown("### 📊 Control de Caja del Edificio")
        st.caption("Resumen interno para el administrador del edificio. Muestra los fondos recaudados con los S/ 30.00 de cada dpto frente a los egresos comunes.")

        col_b1, col_b2, col_b3 = st.columns(3)
        col_b1.metric(
            "💰 Total Recaudado (Cuotas)",
            f"S/ {balance_admin['total_ingresos_cuotas']:.2f}",
            "12 dptos × S/ 30.00"
        )
        col_b2.metric(
            "💸 Total Egresos del Mes",
            f"S/ {balance_admin['total_egresos']:.2f}",
            "Luz común + Limpieza + Internet"
        )
        delta_color = "normal" if balance_admin["saldo_mes"] >= 0 else "inverse"
        col_b3.metric(
            "💵 Saldo Neto del Mes (Caja)",
            f"S/ {balance_admin['saldo_mes']:.2f}",
            "Fondo de reserva disponible"
        )

        st.divider()

        st.markdown("#### 📋 Detalle de Egresos que Cubre el Mantenimiento:")
        col_eg1, col_eg2 = st.columns(2)

        with col_eg1:
            st.write(f"⚡ **Luz de Áreas Comunes:** S/ {soles_luz_comun:.2f}")
            st.caption(f"*(Calculado: Recibo Luz S/ {monto_luz_input:.2f} menos Luz 601 S/ {soles_luz_601:.2f} y Luz 602 S/ {soles_luz_602:.2f})*")

        with col_eg2:
            st.session_state.costo_limpieza = st.number_input(
                "🧹 Gasto en Limpieza (S/.)",
                value=float(st.session_state.costo_limpieza),
                step=10.0,
                format="%.2f"
            )
            st.session_state.costo_internet = st.number_input(
                "📶 Gasto en Internet del Edificio (S/.)",
                value=float(st.session_state.costo_internet),
                step=10.0,
                format="%.2f"
            )

        st.info(f"""
        **Resumen Financiero del Mes:**
        - **Ingresos por cuotas de mantenimiento:** 12 × S/ 30.00 = **S/ {balance_admin['total_ingresos_cuotas']:.2f}**
        - **Total de egresos pagados:** **S/ {balance_admin['total_egresos']:.2f}**
        - **Saldo a favor en caja:** **S/ {balance_admin['saldo_mes']:.2f}**
        """)

    st.divider()

    # -------------------------------------------------------------
    # PASO 4: GUARDAR MES Y EXPORTAR
    # -------------------------------------------------------------
    st.subheader("4. 💾 Guardar Mes y Cerrar Ciclo")
    st.caption("Al guardar, estas lecturas pasarán a ser el mes anterior para el siguiente cobro.")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        if st.button("💾 Guardar este Mes en el Historial", type="primary", use_container_width=True):
            periodo_guardar = datetime.now().strftime("%Y-%m")
            nombre_guardar = datetime.now().strftime("%B %Y").capitalize()
            guardar_mes(
                periodo=periodo_guardar,
                nombre_mes=nombre_guardar,
                agua_total=monto_agua_input,
                luz_total=monto_luz_input,
                luz_kwh=kwh_luz_input,
                lecturas_agua=st.session_state.lecturas_agua_detectadas,
                lecturas_luz=st.session_state.lecturas_luz_detectadas
            )
            st.success(f"✅ ¡Guardado con éxito! Para el siguiente mes, las lecturas base serán las de este periodo.")

    with col_s2:
        df_export = pd.DataFrame(cobranza_vecinos)
        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar Resumen de Cobranza (CSV)",
            data=csv_bytes,
            file_name=f"COBRANZA_ROSARIO_{datetime.now().strftime('%Y_%m')}.csv",
            mime="text/csv",
            use_container_width=True
        )

except Exception as err:
    st.error("⚠️ Se produjo un error al ejecutar la aplicación:")
    st.exception(err)
    st.text(traceback.format_exc())
