# checkeo-service

Pasarela de pagos central del sistema Ticketeo. Recibe solicitudes de pago, valida la tarjeta contra el servicio correspondiente (Visa o Mastercard) y registra transacciones. También expone endpoints de tesorería para reportes y liquidación.

## Arquitectura

Este servicio actúa como orquestador: delega la validación de tarjetas a `visa-service` y `mastercard-service` mediante HTTP, y persiste todas las transacciones en su propia base de datos PostgreSQL.

```
checkeo-service (8000)
    ├── POST /pagos           → valida con visa-service o mastercard-service
    ├── GET  /tesoreria/reporte
    └── POST /tesoreria/liquidar
```

## Requisitos

- Python 3.11+
- PostgreSQL corriendo localmente
- `visa-service` corriendo en el puerto 8001
- `mastercard-service` corriendo en el puerto 8002

## Configuración

Crea un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql+psycopg://postgres:12345@localhost:5432/pasarela_db
VISA_SERVICE_URL=http://localhost:8001
MASTERCARD_SERVICE_URL=http://localhost:8002
```

## Instalación y ejecución

```bash
# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE pasarela_db;"

# Cargar datos de prueba (opcional)
psql -U postgres -d pasarela_db -f seeds.sql

# Iniciar el servidor (las tablas se crean automáticamente al arrancar)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

### `POST /pagos`

Crea un pago. Valida la tarjeta contra el servicio externo correspondiente.

**Body:**
```json
{
  "usuario": "juan123",
  "tipo_tarjeta": "visa",
  "numero_tarjeta": "4111111111111111",
  "valor": 1500.00,
  "empresa_id": 1
}
```

`tipo_tarjeta` acepta `"visa"` o `"mastercard"`.

**Respuesta exitosa (201):**
```json
{
  "id": 1,
  "usuario": "juan123",
  "tipo_tarjeta": "visa",
  "numero_tarjeta": "4111111111111111",
  "valor": 1500.0,
  "empresa_id": 1,
  "estado_pago": "No Liquidado",
  "estado_cobro": "Exitoso",
  "fecha": "2026-05-06T10:00:00"
}
```

---

### `GET /tesoreria/reporte`

Retorna todas las transacciones exitosas y no liquidadas de una empresa, con el total acumulado.

**Query params:**
| Param | Tipo | Requerido |
|---|---|---|
| `empresa_id` | int | Sí |
| `fecha_inicio` | date (YYYY-MM-DD) | No |
| `fecha_fin` | date (YYYY-MM-DD) | No |

---

### `POST /tesoreria/liquidar`

Marca transacciones como liquidadas.

**Body:**
```json
{
  "empresa_id": 1,
  "transaccion_ids": [1, 2, 3]
}
```

## Datos de prueba

El archivo `seeds.sql` carga:

| id | nombre | autorizada |
|---|---|---|
| 1 | Ticketeo S.A. | 1 (activa) |
| 2 | Empresa Bloqueada | 0 (bloqueada) |

## Especificación OpenAPI

Disponible en: `GET /openapi.json`
