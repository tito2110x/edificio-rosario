import json
import os

historico_path = r"C:\Users\User\.gemini\antigravity-ide\scratch\edificio-rosario-app\data\historico_edificio.json"

data_inicial = {
    "edificio": "Rosario del Solar",
    "suministro_agua": "2675620",
    "suministro_luz": "2297829",
    "meses": {
        "2026-08": {
            "nombre": "Agosto 2026",
            "agua_recibo_total": 1018.90,
            "luz_recibo_total": 282.60,
            "luz_kwh_total": 349.90,
            "lecturas_agua": {
                "101": 251016,
                "102": 299920,
                "201": 192198,
                "202": 144789,
                "301": 289720,
                "302": 228653,
                "401": 100844,
                "402": 132679,
                "501": 143870,
                "502": 76590,
                "601": 126516,
                "602": 67697
            },
            "lecturas_luz": {
                "601": 1346.4,
                "602": 1339.3
            }
        },
        "2026-09": {
            "nombre": "Setiembre 2026",
            "agua_recibo_total": 981.00,
            "luz_recibo_total": 329.50,
            "luz_kwh_total": 394.20,
            "lecturas_agua": {
                "101": 256255,
                "102": 313123,
                "201": 201399,
                "202": 151241,
                "301": 299635,
                "302": 237633,
                "401": 108773,
                "402": 141962,
                "501": 153816,
                "502": 81161,
                "601": 139924,
                "602": 73704
            },
            "lecturas_luz": {
                "601": 1459.3,
                "602": 1481.2
            }
        }
    }
}

with open(historico_path, "w", encoding="utf-8") as f:
    json.dump(data_inicial, f, indent=2, ensure_ascii=False)

print("Saved historico_edificio.json successfully!")
