from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, time
from app.db.database import get_db
from app.models.models import Empresa, Transaccion

router = APIRouter()


@router.get("/tesoreria/reporte")
def reporte(
    empresa_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(status_code=400, detail="fecha_inicio debe ser menor o igual a fecha_fin")

    query = db.query(Transaccion).filter(
        Transaccion.empresa_id == empresa_id,
        Transaccion.estado_pago == "No Liquidado",
        Transaccion.estado_cobro == "Exitoso",
    )

    if fecha_inicio:
        query = query.filter(Transaccion.fecha >= datetime.combine(fecha_inicio, time.min))
    if fecha_fin:
        query = query.filter(Transaccion.fecha <= datetime.combine(fecha_fin, time.max))

    transacciones = query.all()
    total = sum(t.valor for t in transacciones)

    return {
        "empresa_id": empresa_id,
        "empresa_nombre": empresa.nombre,
        "total": total,
        "transacciones": [
            {
                "id": t.id,
                "usuario": t.usuario,
                "tipo_tarjeta": t.tipo_tarjeta,
                "numero_tarjeta": t.numero_tarjeta,
                "valor": t.valor,
                "estado_pago": t.estado_pago,
                "estado_cobro": t.estado_cobro,
                "fecha": t.fecha,
            }
            for t in transacciones
        ],
    }
