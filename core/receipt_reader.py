import urllib.request
import json
import base64
import re
from config import GEMINI_API_KEY, PRIMARY_MODEL, FALLBACK_MODELS, obtener_gemini_api_key
from core.gemini_reader import optimizar_imagen

def parsear_numero(val) -> float:
    """Convierte cadenas con símbolos de moneda o comas a float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("S/", "").replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        nums = re.findall(r"\d+\.?\d*", s)
        return float(nums[0]) if nums else 0.0

def analizar_recibo_luz(image_bytes: bytes, mime_type: str = "image/jpeg", api_key: str = None) -> dict:
    """
    Analiza una foto del recibo de Luz del Sur.
    Extrae el total a pagar en soles, la energía a facturar (kWh) y el mes.
    """
    api_key = api_key or obtener_gemini_api_key()
    if mime_type.startswith("image/"):
        opt_bytes, opt_mime = optimizar_imagen(image_bytes, max_dim=1800, quality=90)
    else:
        opt_bytes, opt_mime = image_bytes, mime_type

    b64_data = base64.b64encode(opt_bytes).decode("utf-8")

    prompt = (
        "Analiza este recibo de Luz del Sur (electricidad) de Perú.\n"
        "Extrae OBLIGATORIAMENTE en formato JSON con llaves exactas:\n"
        "{\n"
        "  \"total_a_pagar\": 329.50,\n"
        "  \"energia_facturada_kwh\": 394.20,\n"
        "  \"mes_facturado\": \"Setiembre 2026\",\n"
        "  \"suministro\": \"2297829\",\n"
        "  \"confianza\": \"alta\"\n"
        "}\n"
        "En 'total_a_pagar' busca el recuadro grande amarillo o final 'TOTAL A PAGAR S/'.\n"
        "En 'energia_facturada_kwh' busca 'Energía a facturar (kWh)' o 'Diferencia de lecturas'."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": opt_mime, "data": b64_data}}
            ]
        }],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}
    }

    modelos = [PRIMARY_MODEL] + FALLBACK_MODELS
    for mod in modelos:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cand = data["candidates"][0]["content"]["parts"][0]["text"]
                res = json.loads(cand)
                res["total_a_pagar"] = parsear_numero(res.get("total_a_pagar", 0.0))
                res["energia_facturada_kwh"] = parsear_numero(res.get("energia_facturada_kwh", 0.0))
                return res
        except Exception:
            continue

    return {
        "total_a_pagar": 0.0,
        "energia_facturada_kwh": 0.0,
        "mes_facturado": "",
        "suministro": "",
        "confianza": "error"
    }

def analizar_recibo_agua(image_bytes: bytes, mime_type: str = "image/jpeg", api_key: str = None) -> dict:
    """
    Analiza una foto del recibo de Sedapal (agua).
    Extrae el total a pagar en soles, el mes facturado y el suministro.
    """
    api_key = api_key or obtener_gemini_api_key()
    if mime_type.startswith("image/"):
        opt_bytes, opt_mime = optimizar_imagen(image_bytes, max_dim=1800, quality=90)
    else:
        opt_bytes, opt_mime = image_bytes, mime_type

    b64_data = base64.b64encode(opt_bytes).decode("utf-8")

    prompt = (
        "Analiza este recibo de Sedapal (Agua Potable) de Perú.\n"
        "Extrae OBLIGATORIAMENTE en formato JSON con llaves exactas:\n"
        "{\n"
        "  \"total_a_pagar\": 981.00,\n"
        "  \"mes_facturado\": \"Setiembre 2026\",\n"
        "  \"volumen_facturado_m3\": 104.0,\n"
        "  \"suministro\": \"2675620\",\n"
        "  \"confianza\": \"alta\"\n"
        "}\n"
        "En 'total_a_pagar' busca 'TOTAL A PAGAR S/' o 'Total del mes'."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": opt_mime, "data": b64_data}}
            ]
        }],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}
    }

    modelos = [PRIMARY_MODEL] + FALLBACK_MODELS
    for mod in modelos:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cand = data["candidates"][0]["content"]["parts"][0]["text"]
                res = json.loads(cand)
                res["total_a_pagar"] = parsear_numero(res.get("total_a_pagar", 0.0))
                res["volumen_facturado_m3"] = parsear_numero(res.get("volumen_facturado_m3", 0.0))
                return res
        except Exception:
            continue

    return {
        "total_a_pagar": 0.0,
        "mes_facturado": "",
        "volumen_facturado_m3": 0.0,
        "suministro": "",
        "confianza": "error"
    }
