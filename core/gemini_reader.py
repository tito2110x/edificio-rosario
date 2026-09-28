import urllib.request
import urllib.error
import json
import base64
import re
import io
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from config import GEMINI_API_KEY, PRIMARY_MODEL, FALLBACK_MODELS, obtener_gemini_api_key

def optimizar_imagen(image_bytes: bytes, max_dim: int = 1600, quality: int = 85) -> tuple[bytes, str]:
    """Optimiza y redimensiona la imagen para enviar a la API de forma rápida."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_dim:
            ratio = max_dim / float(max(w, h))
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality)
        return out.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, "image/jpeg"

def normalizar_dpto(texto_dpto: str) -> str:
    """Extrae el número limpio de departamento (ej. '101', '602', etc.)."""
    if not texto_dpto:
        return ""
    texto = str(texto_dpto).strip()
    match = re.search(r"\b(101|102|201|202|301|302|401|402|501|502|601|602)\b", texto)
    if match:
        return match.group(1)
    if "comun" in texto.lower():
        return "Areas comunes"
    digitos = re.findall(r"\d+", texto)
    return digitos[0] if digitos else texto

def invocar_gemini_vision(model_name: str, prompt: str, mime_type: str, b64_data: str, api_key: str, timeout: int = 15) -> dict:
    """Realiza la llamada HTTP a la API de Gemini para un modelo específico."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": b64_data}}
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))
        candidate = resp_data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(candidate)

def analizar_foto_medidor(image_bytes: bytes, api_key: str = None) -> dict:
    """
    Envía la foto a Gemini. Intenta primero con gemini-3.8-flash,
    y si falla o da 503/timeout, conmuta automáticamente a gemini-3.6-flash.
    """
    api_key = api_key or obtener_gemini_api_key()
    opt_bytes, mime_type = optimizar_imagen(image_bytes)
    b64_data = base64.b64encode(opt_bytes).decode("utf-8")

    prompt = (
        "Eres un asistente experto en lectura de medidores de agua y luz de edificios residenciales.\n"
        "Analiza esta fotografía y extrae:\n"
        "1. El número del departamento identificado en etiquetas, cintas adhesivas con marcador, o marcas en la pared/tubería (ej. 101, 102, 201, 202, 301, 302, 401, 402, 501, 502, 601, 602, o 'Luz 601', 'Luz 602', 'Areas comunes').\n"
        "2. La lectura numérica exacta que marca el contador o contómetro:\n"
        "   - En medidores de agua de rodillos (como Fratelli), los rodillos negros corresponden a m3 enteros y los rodillos rojos corresponden a decimales/litros.\n"
        "   - Devuelve la lectura consolidada como número entero (ejemplo: si marca 00251 en negro y 016 en rojo, la lectura es 251016 o 251.016).\n"
        "   - En medidores digitales o de luz, indica los números visibles.\n"
        "3. Tipo de medidor: 'agua' o 'luz'.\n"
        "4. Grado de confianza: 'alta', 'media' o 'baja'.\n\n"
        "Responde OBLIGATORIAMENTE en formato JSON con la siguiente estructura exacta:\n"
        "{\n"
        "  \"departamento\": \"101\",\n"
        "  \"tipo\": \"agua\",\n"
        "  \"lectura_entera\": 251016,\n"
        "  \"lectura_decimal\": 251.016,\n"
        "  \"confianza\": \"alta\",\n"
        "  \"descripcion\": \"Breve descripción de los dígitos vistos y la etiqueta\"\n"
        "}"
    )

    modelos_a_intentar = [PRIMARY_MODEL] + FALLBACK_MODELS

    for modelo in modelos_a_intentar:
        try:
            data = invocar_gemini_vision(modelo, prompt, mime_type, b64_data, api_key, timeout=12)
            data["departamento"] = normalizar_dpto(data.get("departamento", ""))
            data["modelo_usado"] = modelo
            return data
        except Exception:
            # Fallback al siguiente modelo de la lista si hay error o timeout
            continue

    return {
        "departamento": "",
        "tipo": "agua",
        "lectura_entera": 0,
        "lectura_decimal": 0.0,
        "confianza": "error",
        "descripcion": "No se pudo leer la imagen con los modelos de IA disponibles."
    }

def procesar_lote_fotos(fotos_dict: dict[str, bytes], api_key: str = None, max_workers: int = 4) -> dict[str, dict]:
    """Procesa un lote de fotos en paralelo y retorna un diccionario mapeado por nombre de archivo."""
    api_key = api_key or obtener_gemini_api_key()
    resultados = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {
            executor.submit(analizar_foto_medidor, img_bytes, api_key): name
            for name, img_bytes in fotos_dict.items()
        }
        for fut in futuros:
            nombre_archivo = futuros[fut]
            try:
                res = fut.result()
                res["archivo_original"] = nombre_archivo
                resultados[nombre_archivo] = res
            except Exception as e:
                resultados[nombre_archivo] = {
                    "departamento": "",
                    "tipo": "agua",
                    "lectura_entera": 0,
                    "lectura_decimal": 0.0,
                    "confianza": "error",
                    "descripcion": str(e),
                    "archivo_original": nombre_archivo
                }
    return resultados
