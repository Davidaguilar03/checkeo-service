from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from app.db.database import get_db
from app.models.models import Empresa, Transaccion

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
    empresa = db.query(Empresa).filter(Empresa.id == pago.empresa_id).first()
    if not empresa or empresa.autorizada != 1:
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

    tipo = pago.tipo_tarjeta.lower()
    if tipo == "visa":
        url = f"{VISA_SERVICE_URL}/visa/validar"
    elif tipo == "mastercard":
        url = f"{MASTERCARD_SERVICE_URL}/mastercard/validar"
    else:
        transaccion.estado_cobro = "No Exitoso"
        db.commit()
        raise HTTPException(status_code=402, detail="Tipo de tarjeta no soportado")

    valido = False
    try:
        response = httpx.get(
            url,
            params={"numero_tarjeta": pago.numero_tarjeta, "usuario": pago.usuario},
            timeout=10.0,
        )
        valido = response.json().get("valido", False)
    except Exception:
        valido = False

    if valido:
        transaccion.estado_cobro = "Exitoso"
        db.commit()
        db.refresh(transaccion)
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
    raise HTTPException(status_code=402, detail="Pago rechazado")
t