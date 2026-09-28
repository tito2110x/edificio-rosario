import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "historico_edificio.json")

def cargar_historico() -> dict:
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"edificio": "Rosario del Solar", "meses": {}}

def obtener_ultimo_periodo() -> tuple[str, dict]:
    """Retorna la tupla ('2026-09', datos_mes) del último mes registrado."""
    hist = cargar_historico()
    meses = hist.get("meses", {})
    if not meses:
        return "", {}
    ult_clave = sorted(meses.keys())[-1]
    return ult_clave, meses[ult_clave]

def obtener_lecturas_base() -> tuple[str, dict[str, float], dict[str, float]]:
    """
    Retorna: (nombre_mes_anterior, lecturas_agua_ant, lecturas_luz_ant)
    """
    periodo, datos = obtener_ultimo_periodo()
    if not datos:
        return "Anterior", {}, {}
    nombre = datos.get("nombre", periodo)
    agua = {k: float(v) for k, v in datos.get("lecturas_agua", {}).items()}
    luz = {k: float(v) for k, v in datos.get("lecturas_luz", {}).items()}
    return nombre, agua, luz

def guardar_mes(periodo: str, nombre_mes: str, agua_total: float, luz_total: float, luz_kwh: float, lecturas_agua: dict, lecturas_luz: dict):
    hist = cargar_historico()
    if "meses" not in hist:
        hist["meses"] = {}
    hist["meses"][periodo] = {
        "nombre": nombre_mes,
        "agua_recibo_total": float(agua_total),
        "luz_recibo_total": float(luz_total),
        "luz_kwh_total": float(luz_kwh),
        "lecturas_agua": {k: float(v) for k, v in lecturas_agua.items()},
        "lecturas_luz": {k: float(v) for k, v in lecturas_luz.items()}
    }
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)
