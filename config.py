import os

def obtener_gemini_api_key():
    """Obtiene la API key de Streamlit Secrets o variables de entorno de forma segura."""
    # 1. Intentar desde st.secrets (Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    # 2. Intentar desde variable de entorno
    return os.environ.get("GEMINI_API_KEY", "")

GEMINI_API_KEY = obtener_gemini_api_key()

# Modelo principal preferido y fallback automático en caso de timeout o 503
PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-flash-latest"]

DEFAULT_EXCEL_PATH = r"C:\Users\User\Desktop\Consumo agua edificio.xlsx"
DEFAULT_HISTORIAL_DIR = r"C:\Users\User\Desktop\Rosario_Historial"

DEPARTAMENTOS = [
    {"dpto": "101", "nombre": "Julio César / Sheyla", "orden": 1},
    {"dpto": "102", "nombre": "Gina", "orden": 2},
    {"dpto": "201", "nombre": "Ana María / Elvira", "orden": 3},
    {"dpto": "202", "nombre": "Marcos", "orden": 4},
    {"dpto": "301", "nombre": "Varynia", "orden": 5},
    {"dpto": "302", "nombre": "Gianella", "orden": 6},
    {"dpto": "401", "nombre": "Marco Taco / Daniela", "orden": 7},
    {"dpto": "402", "nombre": "Javier", "orden": 8},
    {"dpto": "501", "nombre": "Melissa / Silverio", "orden": 9},
    {"dpto": "502", "nombre": "José Luis / GianMarcos", "orden": 10},
    {"dpto": "601", "nombre": "Joanny", "orden": 11},
    {"dpto": "602", "nombre": "Saul", "orden": 12},
]

DEFAULT_GASTOS_COMUNES = {
    "cuota_mantenimiento": 30.0,
    "internet": 150.0,
    "limpieza": 100.0,
}
