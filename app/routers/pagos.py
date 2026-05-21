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
NU_SERVICE_URL = os.getenv("NU_SERVICE_URL", "https://nu-service.onrender.com")


class PagoRequest(BaseModel):
    usuario: str
    tipo_tarjeta: str
    numero_tarjeta: str
    valor: float
    empresa_id: int
    csv: str | None = None


def _mask_card_number(numero_tarjeta: str) -> str:
    if len(numero_tarjeta) <= 4:
        return "*" * len(numero_tarjeta)
    return "*" * (len(numero_tarjeta) - 4) + numero_tarjeta[-4:]


def _build_error(code: str, message: str, provider: str | None = None, details: dict | None = None) -> dict:
    payload = {
        "code": code,
        "message": message,
    }
    if provider:
        payload["provider"] = provider
    if details:
        payload["details"] = details
    return payload


@router.post("/pagos", status_code=201)
def crear_pago(pago: PagoRequest, db: Session = Depends(get_db)):
    log("INFO", "Solicitud de pago recibida", {"usuario": pago.usuario, "tipo_tarjeta": pago.tipo_tarjeta, "valor": pago.valor, "empresa_id": pago.empresa_id})

    empresa = db.query(Empresa).filter(Empresa.id == pago.empresa_id).first()
    if not empresa:
        log("ERROR", "Empresa no encontrada", {"empresa_id": pago.empresa_id})
        raise HTTPException(status_code=404, detail=_build_error(
            "EMPRESA_NO_ENCONTRADA",
            "Empresa no encontrada.",
            details={"empresa_id": pago.empresa_id},
        ))
    if empresa.autorizada != 1:
        log("ERROR", "Empresa no autorizada", {"empresa_id": pago.empresa_id})
        raise HTTPException(status_code=403, detail=_build_error(
            "EMPRESA_NO_AUTORIZADA",
            "Empresa no autorizada para procesar pagos.",
            details={"empresa_id": pago.empresa_id},
        ))

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

    tipo = pago.tipo_tarjeta.lower().strip()
    valido = False
    provider = None
    if tipo == "visa":
        provider = "visa"
        url = f"{VISA_SERVICE_URL}/visa/validar"
        try:
            response = httpx.get(url, params={"numero_tarjeta": pago.numero_tarjeta, "usuario": pago.usuario}, timeout=10.0)
            if response.status_code != 200:
                log("ERROR", "Respuesta HTTP no exitosa de VISA", {"status_code": response.status_code})
                raise HTTPException(status_code=502, detail=_build_error(
                    "PROVEEDOR_HTTP_ERROR",
                    "El servicio de validacion VISA respondio con error.",
                    provider="VISA",
                    details={"status_code": response.status_code},
                ))
            try:
                data = response.json()
            except Exception:
                log("ERROR", "Respuesta no JSON de VISA", {"body": response.text})
                raise HTTPException(status_code=502, detail=_build_error(
                    "RESPUESTA_PROVEEDOR_INVALIDA",
                    "El servicio de validacion VISA devolvio una respuesta invalida.",
                    provider="VISA",
                ))
            valido = data.get("valid", data.get("valido", False))
            log("INFO", "Respuesta de VISA", {"valido": valido})
        except HTTPException:
            raise
        except Exception as e:
            log("ERROR", f"Error al conectar con servicio {tipo}", {"error": str(e)})
            raise HTTPException(status_code=503, detail=_build_error(
                "PROVEEDOR_NO_DISPONIBLE",
                "No se pudo contactar el servicio de validacion VISA.",
                provider="VISA",
            ))
    elif tipo == "mastercard":
        provider = "mastercard"
        url = f"{MASTERCARD_SERVICE_URL}/mastercard/validar"
        try:
            response = httpx.get(url, params={"numero_tarjeta": pago.numero_tarjeta, "usuario": pago.usuario}, timeout=10.0)
            if response.status_code != 200:
                log("ERROR", "Respuesta HTTP no exitosa de MASTERCARD", {"status_code": response.status_code})
                raise HTTPException(status_code=502, detail=_build_error(
                    "PROVEEDOR_HTTP_ERROR",
                    "El servicio de validacion Mastercard respondio con error.",
                    provider="MASTERCARD",
                    details={"status_code": response.status_code},
                ))
            try:
                data = response.json()
            except Exception:
                log("ERROR", "Respuesta no JSON de MASTERCARD", {"body": response.text})
                raise HTTPException(status_code=502, detail=_build_error(
                    "RESPUESTA_PROVEEDOR_INVALIDA",
                    "El servicio de validacion Mastercard devolvio una respuesta invalida.",
                    provider="MASTERCARD",
                ))
            valido = data.get("valid", data.get("valido", False))
            log("INFO", "Respuesta de Mastercard", {"valido": valido})
        except HTTPException:
            raise
        except Exception as e:
            log("ERROR", f"Error al conectar con servicio {tipo}", {"error": str(e)})
            raise HTTPException(status_code=503, detail=_build_error(
                "PROVEEDOR_NO_DISPONIBLE",
                "No se pudo contactar el servicio de validacion Mastercard.",
                provider="MASTERCARD",
            ))
    elif tipo == "nubank":
        provider = "nubank"
        if not pago.csv:
            log("ERROR", "CSV requerido para Nubank", {"usuario": pago.usuario})
            raise HTTPException(status_code=400, detail=_build_error(
                "CSV_REQUERIDO",
                "El campo csv es requerido para validar tarjetas Nubank.",
                provider="NUBANK",
            ))
        url = f"{NU_SERVICE_URL}/validate"
        try:
            response = httpx.post(url, json={"number": pago.numero_tarjeta, "csv": pago.csv, "token": 2000}, timeout=10.0)
            if response.status_code != 200:
                log("ERROR", "Respuesta HTTP no exitosa de NUBANK", {"status_code": response.status_code})
                raise HTTPException(status_code=502, detail=_build_error(
                    "PROVEEDOR_HTTP_ERROR",
                    "El servicio de validacion Nubank respondio con error.",
                    provider="NUBANK",
                    details={"status_code": response.status_code},
                ))
            text = response.text.strip()
            if text == "VALID":
                valido = True
            else:
                try:
                    data = response.json()
                    valido = data.get("valid", data.get("valido", False))
                except Exception:
                    log("ERROR", "Respuesta no valida de NUBANK", {"body": response.text})
                    valido = False
            log("INFO", "Respuesta de nubank", {"valido": valido})
        except HTTPException:
            raise
        except Exception as e:
            log("ERROR", "Error al conectar con servicio nubank", {"error": str(e)})
            raise HTTPException(status_code=503, detail=_build_error(
                "PROVEEDOR_NO_DISPONIBLE",
                "No se pudo contactar el servicio de validacion Nubank.",
                provider="NUBANK",
            ))
    else:
        transaccion.estado_cobro = "No Exitoso"
        db.commit()
        log("ERROR", "Tipo de tarjeta no soportado", {"tipo_tarjeta": pago.tipo_tarjeta})
        raise HTTPException(status_code=400, detail=_build_error(
            "TARJETA_NO_SOPORTADA",
            "Tipo de tarjeta no soportado. Use VISA, Mastercard o Nubank.",
            details={"tipo_tarjeta": pago.tipo_tarjeta},
        ))

    if valido:
        transaccion.estado_cobro = "Exitoso"
        db.commit()
        db.refresh(transaccion)
        log("INFO", "Pago exitoso", {"transaccion_id": transaccion.id, "usuario": pago.usuario})
        return {
            "id": transaccion.id,
            "usuario": transaccion.usuario,
            "tipo_tarjeta": transaccion.tipo_tarjeta,
            "numero_tarjeta": _mask_card_number(transaccion.numero_tarjeta),
            "valor": transaccion.valor,
            "empresa_id": transaccion.empresa_id,
            "estado_pago": transaccion.estado_pago,
            "estado_cobro": transaccion.estado_cobro,
            "fecha": transaccion.fecha,
            "code": "PAGO_EXITOSO",
            "message": "Pago validado por el proveedor.",
            "provider": (provider or "desconocido").upper(),
        }

    transaccion.estado_cobro = "No Exitoso"
    db.commit()
    log("ERROR", "Pago rechazado", {"transaccion_id": transaccion.id, "usuario": pago.usuario})
    raise HTTPException(status_code=402, detail=_build_error(
        "PAGO_RECHAZADO",
        "El proveedor rechazo la tarjeta durante la validacion.",
        provider=(provider or "desconocido").upper(),
        details={
            "transaccion_id": transaccion.id,
            "numero_tarjeta": _mask_card_number(transaccion.numero_tarjeta),
        },
    ))