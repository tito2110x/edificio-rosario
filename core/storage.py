import os
import json
from config import DEFAULT_HISTORIAL_DIR

def inicializar_almacenamiento(base_dir: str = DEFAULT_HISTORIAL_DIR):
    """Crea la estructura de carpetas si no existe."""
    os.makedirs(base_dir, exist_ok=True)

def guardar_fotos_mes(
    periodo: str,
    fotos_por_dpto: dict[str, bytes],
    base_dir: str = DEFAULT_HISTORIAL_DIR
) -> dict[str, str]:
    """
    Guarda las fotos del mes en una subcarpeta periodo (ej. '2026-09')
    organizadas por número de departamento (ej. '101.jpg').
    Retorna un diccionario {dpto: ruta_guardada}.
    """
    mes_dir = os.path.join(base_dir, periodo)
    os.makedirs(mes_dir, exist_ok=True)

    rutas = {}
    for dpto, img_bytes in fotos_por_dpto.items():
        if not img_bytes:
            continue
        filename = f"{dpto}.jpg"
        filepath = os.path.join(mes_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        rutas[dpto] = filepath

    return rutas

def guardar_registro_mes(periodo: str, datos: dict, base_dir: str = DEFAULT_HISTORIAL_DIR):
    """Guarda el resumen de cálculos y lecturas del mes en JSON para respaldo permanente."""
    mes_dir = os.path.join(base_dir, periodo)
    os.makedirs(mes_dir, exist_ok=True)
    json_path = os.path.join(mes_dir, "resumen_calculos.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def obtener_lecturas_historicas(base_dir: str = DEFAULT_HISTORIAL_DIR) -> dict[str, dict]:
    """Retorna los datos guardados de meses anteriores."""
    if not os.path.exists(base_dir):
        return {}
    periodos = sorted([p for p in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, p))])
    historial = {}
    for p in periodos:
        j_path = os.path.join(base_dir, p, "resumen_calculos.json")
        if os.path.exists(j_path):
            try:
                with open(j_path, "r", encoding="utf-8") as f:
                    historial[p] = json.load(f)
            except Exception:
                pass
    return historial
