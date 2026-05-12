from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    autorizada = Column(Integer, nullable=False)


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, nullable=False)
    tipo_tarjeta = Column(String, nullable=False)
    numero_tarjeta = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    estado_pago = Column(String, nullable=False, default="No Liquidado")
    estado_cobro = Column(String, nullable=True)
    fecha = Column(DateTime, server_default=func.now())
