import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime

from config import (
    obtener_gemini_api_key, PRIMARY_MODEL,
    DEPARTAMENTOS, DEFAULT_GASTOS_COMUNES
)
from core.gemini_reader import procesar_lote_fotos
from core.receipt_reader import analizar_recibo_luz, analizar_recibo_agua
from core.calculator import calcular_prorrateo_agua, calcular_resumen_general
from core.database import obtener_lecturas_base, guardar_mes

# Configuración de página
st.set_page_config(
    page_title="Rosario del Solar - Cobranza Mensual",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Mobile-First
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    .main-header {
        background: linear-gradient(90deg, #0E4A85 0%, #1A73E8 100%);
        color: white;
        padding: 18px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        font-size: 1.8rem;
        margin: 0;
        font-weight: 700;
    }
    .main-header p {
        color: #E3F2FD;
        margin: 5px 0 0 0;
        font-size: 0.95rem;
    }
    .badge-total {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 6px 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.15rem;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado
st.markdown("""
<div class="main-header">
    <h1>🏢 Edificio Rosario del Solar</h1>
    <p>Cobranza mensual automatizada de Agua, Luz y Mantenimiento desde el celular</p>
</div>
""", unsafe_allow_html=True)

# Gestión de API Key
api_key_detectada = obtener_gemini_api_key()

with st.sidebar:
    st.subheader("⚙️ Configuración")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=api_key_detectada,
        type="password",
        help="Pega aquí tu API Key de Google AI Studio (100% gratuita)."
    )
    if not api_key_input:
        st.warning("⚠️ Ingresa tu API Key para habilitar el reconocimiento automático con IA.")
    else:
        st.success("✅ API Key conectada")

# Cargar historial base
nombre_mes_ant, lecturas_agua_ant, lecturas_luz_ant = obtener_lecturas_base()

# Variables en session_state
if "recibo_agua_monto" not in st.session_state:
    st.session_state.recibo_agua_monto = 981.00
if "recibo_luz_monto" not in st.session_state:
    st.session_state.recibo_luz_monto = 329.50
if "recibo_luz_kwh" not in st.session_state:
    st.session_state.recibo_luz_kwh = 394.20
if "lecturas_agua_detectadas" not in st.session_state:
    st.session_state.lecturas_agua_detectadas = lecturas_agua_ant.copy()
if "lecturas_luz_detectadas" not in st.session_state:
    st.session_state.lecturas_luz_detectadas = lecturas_luz_ant.copy()
if "fotos_medidores" not in st.session_state:
    st.session_state.fotos_medidores = {}

# --- PASO 1: SUBIR RECIBOS (FOTOS) ---
st.subheader("1. 📄 Subir Fotos de los Recibos (Agua y Luz)")
st.caption("Sube las fotos de los recibos de Sedapal y Luz del Sur. La IA leerá automáticamente los montos y los kWh.")

col_r1, col_r2 = st.columns(2)

with col_r1:
    foto_recibo_agua = st.file_uploader(
        "💧 Foto Recibo Sedapal (Agua)",
        type=["jpg", "jpeg", "png", "pdf"],
        key="uploader_recibo_agua"
    )
    if foto_recibo_agua:
        if st.button("🤖 Leer Recibo de Agua con IA", key="btn_leer_agua"):
            if not api_key_input:
                st.error("Por favor, ingresa tu Gemini API Key en la barra lateral.")
            else:
                with st.spinner("Leyendo recibo de Sedapal con IA..."):
                    m_type = foto_recibo_agua.type or "image/jpeg"
                    res_a = analizar_recibo_agua(foto_recibo_agua.getvalue(), mime_type=m_type, api_key=api_key_input)
                    if res_a.get("total_a_pagar", 0) > 0:
                        st.session_state.recibo_agua_monto = res_a["total_a_pagar"]
                        st.success(f"✅ Sedapal detectado: S/ {res_a['total_a_pagar']:.2f}")
                    else:
                        st.warning("No se pudo leer el monto automáticamente. Ingresa el valor manual abajo.")

with col_r2:
    foto_recibo_luz = st.file_uploader(
        "⚡ Foto Recibo Luz del Sur",
        type=["jpg", "jpeg", "png", "pdf"],
        key="uploader_recibo_luz"
    )
    if foto_recibo_luz:
        if st.button("🤖 Leer Recibo de Luz con IA", key="btn_leer_luz"):
            if not api_key_input:
                st.error("Por favor, ingresa tu Gemini API Key en la barra lateral.")
            else:
                with st.spinner("Leyendo recibo de Luz del Sur con IA..."):
                    m_type = foto_recibo_luz.type or "image/jpeg"
                    res_l = analizar_recibo_luz(foto_recibo_luz.getvalue(), mime_type=m_type, api_key=api_key_input)
                    if res_l.get("total_a_pagar", 0) > 0:
                        st.session_state.recibo_luz_monto = res_l["total_a_pagar"]
                        st.session_state.recibo_luz_kwh = res_l["energia_facturada_kwh"]
                        st.success(f"✅ Luz detectada: S/ {res_l['total_a_pagar']:.2f} ({res_l['energia_facturada_kwh']:.1f} kWh)")
                    else:
                        st.warning("No se pudo leer el monto automáticamente. Ingresa el valor manual abajo.")

# Campos con los montos detectados (editables)
st.write("**Montos a facturar este mes:**")
c_m1, c_m2, c_m3 = st.columns(3)
with c_m1:
    monto_agua_input = st.number_input("💧 Total Recibo Sedapal (S/.)", value=float(st.session_state.recibo_agua_monto), step=10.0, format="%.2f")
with c_m2:
    monto_luz_input = st.number_input("⚡ Total Recibo Luz (S/.)", value=float(st.session_state.recibo_luz_monto), step=10.0, format="%.2f")
with c_m3:
    kwh_luz_input = st.number_input("⚡ Energía facturada (kWh)", value=float(st.session_state.recibo_luz_kwh), step=5.0, format="%.2f")

st.divider()

# --- PASO 2: SUBIR FOTOS DE LOS MEDIDORES ---
st.subheader("2. 📸 Subir Fotos de los Medidores")
st.caption(f"La IA identificará el sticker con el número de dpto y la lectura actual. La lectura anterior se toma de: **{nombre_mes_ant}**.")

fotos_medidores_files = st.file_uploader(
    "Selecciona todas las fotos de los medidores de golpe (Agua y Luz)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="uploader_medidores_masivo"
)

if fotos_medidores_files:
    st.info(f"📁 {len(fotos_medidores_files)} fotos seleccionadas listas para escanear.")
    if st.button("🚀 Escanear Medidores con IA (Gemini)", type="primary", use_container_width=True):
        if not api_key_input:
            st.error("Por favor, ingresa tu Gemini API Key en la barra lateral.")
        else:
            f_dict = {f.name: f.getvalue() for f in fotos_medidores_files}
            with st.spinner("La IA está leyendo los stickers y números de los medidores..."):
                res_lote = procesar_lote_fotos(f_dict, api_key=api_key_input)
                
                dptos_actualizados = []
                for name, r in res_lote.items():
                    dpto = r.get("departamento")
                    tipo = r.get("tipo", "agua")
                    lectura = float(r.get("lectura_entera", 0))
                    if dpto:
                        st.session_state.fotos_medidores[dpto] = f_dict[name]
                        if dpto in ["601", "602"] and tipo == "luz":
                            st.session_state.lecturas_luz_detectadas[dpto] = float(r.get("lectura_decimal", lectura))
                            dptos_actualizados.append(f"Luz {dpto}")
                        else:
                            st.session_state.lecturas_agua_detectadas[dpto] = lectura
                            dptos_actualizados.append(f"Agua {dpto}")

                st.success(f"✅ Se detectaron con éxito: {', '.join(dptos_actualizados)}")

st.divider()

# --- PASO 3: CÁLCULOS Y RESULTADOS (CUÁNTO DEBE PAGAR CADA UNO) ---
st.subheader("3. 💰 Cobranza Mensual por Departamento")

# Cálculos de Luz
kwh_601 = max(0.0, float(st.session_state.lecturas_luz_detectadas.get("601", 0.0)) - float(lecturas_luz_ant.get("601", 0.0)))
kwh_602 = max(0.0, float(st.session_state.lecturas_luz_detectadas.get("602", 0.0)) - float(lecturas_luz_ant.get("602", 0.0)))
kwh_comun = max(0.0, kwh_luz_input - kwh_601 - kwh_602)

soles_luz_601 = (kwh_601 / kwh_luz_input * monto_luz_input) if kwh_luz_input > 0 else 0.0
soles_luz_602 = (kwh_602 / kwh_luz_input * monto_luz_input) if kwh_luz_input > 0 else 0.0
soles_luz_comun = (kwh_comun / kwh_luz_input * monto_luz_input) if kwh_luz_input > 0 else 0.0

cobros_luz_internos = {
    "601": round(soles_luz_601, 2),
    "602": round(soles_luz_602, 2)
}

# Cálculos de Agua
calculo_agua = calcular_prorrateo_agua(
    lecturas_actuales=st.session_state.lecturas_agua_detectadas,
    lecturas_anteriores=lecturas_agua_ant,
    monto_recibo_sedapal=monto_agua_input
)

resumen_cobranza = calcular_resumen_general(
    calculo_agua=calculo_agua,
    monto_luz_comun=soles_luz_comun,
    gastos_fijos=DEFAULT_GASTOS_COMUNES,
    cobros_luz_internos=cobros_luz_internos
)

# Métricas rápidas
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("💧 Sedapal", f"S/ {monto_agua_input:.2f}", f"Consumo: {calculo_agua['total_consumo']:,.0f} m³")
col_m2.metric("⚡ Luz del Sur", f"S/ {monto_luz_input:.2f}", f"Energía: {kwh_luz_input:.1f} kWh")
col_m3.metric("🏢 Luz Áreas Comunes", f"S/ {soles_luz_comun:.2f}", f"{kwh_comun:.1f} kWh")

# Lista de cobranza departamento por departamento
for item in resumen_cobranza:
    dpto = item["dpto"]
    nombre = item["nombre"]
    agua_s = item["agua_soles"]
    cuota = item["cuota_mantenimiento"]
    luz_prop = item["luz_propia"]
    tot = item["total_a_pagar"]
    cons = item["consumo"]
    act = item["lectura_actual"]
    ant = item["lectura_anterior"]

    detalle_luz = f" + ⚡ Luz propia: S/ {luz_prop:.2f}" if luz_prop > 0 else ""

    msg_wa = (
        f"Hola {nombre} (Dpto {dpto}), te compartimos el detalle de cobranza del mes:\n\n"
        f"💧 Agua ({cons:,.0f} m³): S/ {agua_s:.2f}\n"
        f"🏢 Cuota Mantenimiento: S/ {cuota:.2f}"
        f"{detalle_luz}\n"
        f"👉 TOTAL A PAGAR: S/ {tot:.2f}\n\n"
        f"Muchas gracias por tu puntualidad."
    )

    with st.container(border=True):
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.markdown(f"### Dpto {dpto} - {nombre}")
            st.write(f"💧 **Agua:** S/ {agua_s:.2f} *(Consumo: {cons:,.0f} m³ | Lect. actual: {act:,.0f})*")
            st.write(f"🏢 **Mantenimiento:** S/ {cuota:.2f}{detalle_luz}")
        with col_t2:
            st.markdown(f"<div class='badge-total'>Total: S/ {tot:.2f}</div>", unsafe_allow_html=True)
            st.write("")
            st.text_area("Copiar WhatsApp", value=msg_wa, height=70, key=f"wa_m_{dpto}", label_visibility="collapsed")

st.divider()

# --- PASO 4: GUARDAR Y DESCARGAR EXCEL ---
st.subheader("4. 💾 Guardar Mes y Descargar Resumen")

col_g1, col_g2 = st.columns(2)

with col_g1:
    if st.button("💾 Guardar este mes en el Historial", type="primary", use_container_width=True):
        periodo_actual = datetime.now().strftime("%Y-%m")
        nombre_mes_display = datetime.now().strftime("%B %Y").capitalize()
        guardar_mes(
            periodo=periodo_actual,
            nombre_mes=nombre_mes_display,
            agua_total=monto_agua_input,
            luz_total=monto_luz_input,
            luz_kwh=kwh_luz_input,
            lecturas_agua=st.session_state.lecturas_agua_detectadas,
            lecturas_luz=st.session_state.lecturas_luz_detectadas
        )
        st.success(f"✅ ¡Guardado con éxito! El próximo mes las lecturas anteriores se cargarán automáticamente.")

with col_g2:
    # Generar tabla resumen en CSV / Excel descargable
    df_resumen_export = pd.DataFrame(resumen_cobranza)
    csv_bytes = df_resumen_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Descargar Resumen de Cobranza (CSV)",
        data=csv_bytes,
        file_name=f"COBRANZA_ROSARIO_{datetime.now().strftime('%Y_%m')}.csv",
        mime="text/csv",
        use_container_width=True
    )
