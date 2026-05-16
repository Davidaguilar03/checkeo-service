import json
import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs", "checkeo.log")

def log(nivel: str, mensaje: str, extra: dict = {}):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "servicio": "checkeo",
        "nivel": nivel,
        "mensaje": mensaje,
        **extra
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada) + "\n")