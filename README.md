<div align="center">

# checkeo-service

**Microservicio de pasarela de pagos del ecosistema Ticketeo**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-2094F3?logo=gunicorn&logoColor=white)](https://www.uvicorn.org/)

</div>

---

## Descripción

**checkeo-service** es la **pasarela de pagos central** del sistema Ticketeo. Construido con **FastAPI**, actúa como orquestador de pagos: recibe las solicitudes de cobro, valida la tarjeta contra el emisor correspondiente (Visa o Mastercard) mediante llamadas HTTP, registra cada transacción y expone endpoints de tesorería para la consulta y liquidación de fondos por empresa.

El servicio está pensado como una pieza desacoplada dentro de una arquitectura de microservicios: concentra toda la lógica de pago para que las aplicaciones cliente (como Ticketeo) deleguen el procesamiento sin acoplarse a los detalles de validación de tarjetas.

---

## Características principales

- **Procesamiento de pagos** con validación de tarjeta delegada al emisor correspondiente.
- **Orquestación de servicios externos**: enruta la validación a `visa-service` o `mastercard-service` según el tipo de tarjeta, mediante peticiones HTTP asíncronas (httpx).
- **Persistencia de transacciones** en PostgreSQL mediante SQLAlchemy 2.0, con creación automática de tablas al arranque.
- **Módulo de tesorería**: reportes de transacciones acumuladas por empresa y liquidación de fondos.
- **Configuración por entorno** mediante variables de entorno (`.env`) con python-dotenv.
- **Especificación OpenAPI** expuesta como recurso para integración con clientes.

---

## Arquitectura

El servicio funciona como orquestador central: delega la validación de tarjetas a los servicios de cada emisor y persiste todas las transacciones en su propia base de datos.

```
        Aplicación cliente (Ticketeo)
                    │
                    │ HTTP (solicitud de pago)
                    ▼
        ┌──────────────────────────┐
        │      checkeo-service     │   :8000
        │   FastAPI · SQLAlchemy   │
        │                          │
        │  POST /pagos             │
        │  GET  /tesoreria/reporte │
        │  POST /tesoreria/liquidar│
        └──────┬────────────┬──────┘
               │            │
          HTTP │            │ HTTP
               ▼            ▼
       ┌──────────────┐ ┌────────────────────┐
       │ visa-service │ │ mastercard-service │
       │    :8001     │ │       :8002        │
       └──────────────┘ └────────────────────┘
               │
               ▼
        ┌──────────────┐
        │  PostgreSQL  │   (transacciones)
        └──────────────┘
```

---

## Stack tecnológico

| Categoría | Tecnologías |
|-----------|-------------|
| **Lenguaje** | Python 3.11+ |
| **Framework** | FastAPI |
| **Servidor ASGI** | Uvicorn |
| **ORM / Base de datos** | SQLAlchemy 2.0 + PostgreSQL (psycopg) |
| **Cliente HTTP** | httpx |
| **Configuración** | python-dotenv |

---

## Requisitos previos

- **Python 3.11** o superior
- **PostgreSQL** en ejecución local
- **`visa-service`** corriendo en el puerto `8001`
- **`mastercard-service`** corriendo en el puerto `8002`

---

## Configuración

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
DATABASE_URL=postgresql+psycopg://postgres:12345@localhost:5432/pasarela_db
VISA_SERVICE_URL=http://localhost:8001
MASTERCARD_SERVICE_URL=http://localhost:8002
```

---

## Instalación y ejecución

```bash
# Crear y activar el entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / macOS
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

El servicio quedará disponible en **http://localhost:8000**.

---

## Endpoints

### `POST /pagos`

Crea un pago y valida la tarjeta contra el servicio del emisor correspondiente.

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

Retorna las transacciones exitosas y no liquidadas de una empresa, junto con el total acumulado.

**Query params:**

| Parámetro | Tipo | Requerido |
|-----------|------|-----------|
| `empresa_id` | int | Sí |
| `fecha_inicio` | date (YYYY-MM-DD) | No |
| `fecha_fin` | date (YYYY-MM-DD) | No |

---

### `POST /tesoreria/liquidar`

Marca un conjunto de transacciones como liquidadas.

**Body:**

```json
{
  "empresa_id": 1,
  "transaccion_ids": [1, 2, 3]
}
```

---

## Datos de prueba

El archivo `seeds.sql` carga empresas de ejemplo para validar el flujo de autorización:

| id | nombre | autorizada |
|----|--------|------------|
| 1 | Ticketeo S.A. | 1 (activa) |
| 2 | Empresa Bloqueada | 0 (bloqueada) |

---

## Especificación OpenAPI

La especificación completa está disponible en:

```
GET /openapi.json
```

---

## Estructura del proyecto

```
checkeo-service/
├── app/
│   ├── db/          # Configuración de base de datos y modelos
│   └── routers/     # Routers: pagos, tesoreria
├── main.py          # Punto de entrada de la aplicación FastAPI
├── openapi.json     # Especificación OpenAPI
├── requirements.txt # Dependencias del proyecto
└── seeds.sql        # Datos de prueba
```

---

## Ecosistema Ticketeo

Este servicio es consumido por la aplicación principal [**Ticketeo**](https://github.com/OscarRoa34/Ticketeo) (Spring Boot), que delega en él el procesamiento de los pagos de las entradas.

---

## Autor

Desarrollado por 
[**Oscar Roa**](https://github.com/OscarRoa34).
[**David Aguilar**](https://github.com/Davidaguilar03).
