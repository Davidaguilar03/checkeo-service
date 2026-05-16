from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from app.db.database import get_db
from app.models.models import Empresa, Transaccion
from app.logger import log

load_dotenv()

router = APIRouter()

VISA_SERVICE_URL = os.getenv("VISA_SERVICE_URL", "http://localhost:8001")
MASTERCARD_SERVICE_URL = os.getenv("MASTERCARD_SERVICE_URL", "http://localhost:8002")


class PagoRequest(BaseModel):
    usuario: str
    tipo_tarjeta: str
    numero_tarjeta: str
    valor: float
    empresa_id: int


@router.post("/pagos", status_code=201)
def crear_pago(pago: PagoRequest, db: Session = Depends(get_db)):
    log("INFO", "Solicitud de pago recibida", {"usuario": pago.usuario, "tipo_tarjeta": pago.tipo_tarjeta, "valor": pago.valor, "empresa_id": pago.empresa_id})

    empresa = db.query(Empresa).filter(Empresa.id == pago.empresa_id).first()
    if not empresa or empresa.autorizada != 1:
        log("ERROR", "Empresa no encontrada o no autorizada", {"empresa_id": pago.empresa_id})
        raise HTTPException(status_code=404, detail="Empresa no encontrada o no autorizada")

    transaccion = Transaccion(
        usuario=pago.usuario,
        tipo_tarjeta=pago.tipo_tarjeta,
        numero_tarjeta=pago.numero_tarjeta,
        valor=pago.valor,
        empresa_id=pago.empresa_id,
        estado_pago="No Liquidado",
        estado_cobro=None,
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    log("INFO", "Transacción registrada", {"transaccion_id": transaccion.id})

    tipo = pago.tipo_tarjeta.lower()
    if tipo == "visa":
        url = f"{VISA_SERVICE_URL}/visa/validar"
    elif tipo == "mastercard":
        url = f"{MASTERCARD_SERVICE_URL}/mastercard/validar"
    else:
        transaccion.estado_cobro = "No Exitoso"
        db.commit()
        log("ERROR", "Tipo de tarjeta no soportado", {"tipo_tarjeta": pago.tipo_tarjeta})
        raise HTTPException(status_code=402, detail="Tipo de tarjeta no soportado")

    valido = False
    try:
        response = httpx.get(url, params={"numero_tarjeta": pago.numero_tarjeta, "usuario": pago.usuario}, timeout=10.0)
        data = response.json()
        valido = data.get("valid", data.get("valido", False))
        log("INFO", f"Respuesta de {tipo}", {"valido": valido})
    except Exception as e:
        log("ERROR", f"Error al conectar con servicio {tipo}", {"error": str(e)})
        valido = False

    if valido:
        transaccion.estado_cobro = "Exitoso"
        db.commit()
        db.refresh(transaccion)
        log("INFO", "Pago exitoso", {"transaccion_id": transaccion.id, "usuario": pago.usuario})
        return {
            "id": transaccion.id,
            "usuario": transaccion.usuario,
            "tipo_tarjeta": transaccion.tipo_tarjeta,
            "numero_tarjeta": transaccion.numero_tarjeta,
            "valor": transaccion.valor,
            "empresa_id": transaccion.empresa_id,
            "estado_pago": transaccion.estado_pago,
            "estado_cobro": transaccion.estado_cobro,
            "fecha": transaccion.fecha,
        }

    transaccion.estado_cobro = "No Exitoso"
    db.commit()
    log("ERROR", "Pago rechazado", {"transaccion_id": transaccion.id, "usuario": pago.usuario})
    raise HTTPException(status_code=402, detail="Pago rechazado")