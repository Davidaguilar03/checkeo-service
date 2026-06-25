<div align="center">

# Ticketeo

**Plataforma web para la gestión integral de eventos y venta de entradas**

[![Java](https://img.shields.io/badge/Java-21-orange?logo=openjdk&logoColor=white)](https://www.oracle.com/java/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-4.0-6DB33F?logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Maven](https://img.shields.io/badge/Maven-C71A36?logo=apachemaven&logoColor=white)](https://maven.apache.org/)
[![CI/CD](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white)](https://github.com/OscarRoa34/Ticketeo/actions)

</div>

---

## Descripción

**Ticketeo** es una aplicación web full-stack para la **gestión de eventos**: creación y administración de eventos, venta de entradas y emisión de tiquetes con código QR. Está construida sobre **Spring Boot 4** con persistencia en **PostgreSQL** y un frontend renderizado del lado del servidor con **Thymeleaf**.

El proyecto sigue una arquitectura orientada a servicios: la aplicación principal gestiona los eventos y las entradas, mientras que el cobro de las compras se delega a un **microservicio de pasarela de pagos independiente** que valida tarjetas y registra transacciones. Esto permite desacoplar la lógica de negocio del procesamiento de pagos y trabajar con un modelo cercano a un entorno productivo real.

---

## Características principales

- **Gestión completa de eventos y entradas**, con persistencia automática mediante Spring Data JPA / Hibernate.
- **Autenticación y autorización por roles** con Spring Security (rol `ADMIN` y usuarios estándar).
- **Integración con pasarela de pagos externa** para el procesamiento de cobros con tarjeta (ver sección de integración).
- **Emisión de tiquetes en PDF** mediante OpenPDF.
- **Generación de códigos QR** para la validación de entradas, usando Google ZXing.
- **Comunicación en tiempo real** a través de WebSocket.
- **Mensajería asíncrona** con RabbitMQ (Spring AMQP) para procesos desacoplados.
- **Interfaz web** renderizada con Thymeleaf e integración de seguridad en plantillas.
- **Pruebas automatizadas** unitarias, de integración y end-to-end con Playwright.
- **Aseguramiento de calidad** con cobertura de código (JaCoCo) y análisis estático (SonarQube).
- **Integración y entrega continua** mediante GitHub Actions.

---

## Arquitectura

Ticketeo opera como la aplicación central de un ecosistema de servicios. Para el procesamiento de pagos, se comunica vía HTTP con un microservicio de pasarela ([`checkeo-service`](https://github.com/Davidaguilar03/checkeo-service)), que a su vez orquesta la validación contra los emisores de tarjetas.

```
                 ┌──────────────────────────┐
                 │        Ticketeo          │
                 │  Spring Boot · Java 21   │
                 │  Gestión de eventos y    │
                 │     venta de entradas    │
                 └────────────┬─────────────┘
                              │ HTTP (solicitud de pago)
                              ▼
                 ┌──────────────────────────┐
                 │      checkeo-service     │
                 │   Pasarela de pagos      │
                 │   (FastAPI · Python)     │
                 │   /pagos · /tesoreria    │
                 └──────┬────────────┬──────┘
                        │            │
                   HTTP │            │ HTTP
                        ▼            ▼
                ┌──────────────┐ ┌──────────────────┐
                │ visa-service │ │ mastercard-service │
                └──────────────┘ └──────────────────┘
```

---

## Integración con la pasarela de pagos

El cobro de las entradas se procesa a través de [`checkeo-service`](https://github.com/Davidaguilar03/checkeo-service), una pasarela de pagos independiente desarrollada en **FastAPI (Python)**. Ticketeo envía las solicitudes de pago vía HTTP y la pasarela se encarga de:

- **Validar la tarjeta** delegando en el servicio del emisor correspondiente (Visa o Mastercard).
- **Registrar y persistir** cada transacción en su propia base de datos.
- **Exponer endpoints de tesorería** para reportes de transacciones y liquidación de fondos por empresa.

Endpoints principales consumidos:

| Método | Endpoint | Función |
|--------|----------|---------|
| `POST` | `/pagos` | Procesa el pago de una compra y valida la tarjeta |
| `GET`  | `/tesoreria/reporte` | Consulta transacciones y total acumulado por empresa |
| `POST` | `/tesoreria/liquidar` | Marca transacciones como liquidadas |

> Para ejecutar el flujo completo de pagos en local, la pasarela y sus servicios asociados deben estar levantados (`checkeo-service` en el puerto `8000`, junto a `visa-service` y `mastercard-service`). Consulta el repositorio de la pasarela para su configuración.

---

## Stack tecnológico

| Categoría | Tecnologías |
|-----------|-------------|
| **Lenguaje** | Java 21 |
| **Framework** | Spring Boot 4 (Web MVC, Data JPA, Security, WebSocket, AMQP) |
| **Base de datos** | PostgreSQL + Hibernate |
| **Frontend** | Thymeleaf, HTML, CSS, JavaScript |
| **Documentos / QR** | OpenPDF, Google ZXing |
| **Mensajería** | RabbitMQ |
| **Integración externa** | Pasarela de pagos `checkeo-service` (HTTP / REST) |
| **Testing** | Spring Boot Test, Spring Security Test, Playwright |
| **Calidad** | JaCoCo, SonarQube |
| **Build / CI** | Maven (Wrapper), GitHub Actions |
| **Utilidades** | Lombok |

---

## Requisitos previos

- **Java 21** o superior — [Descargar JDK 21](https://www.oracle.com/java/technologies/javase/jdk21-archive-downloads.html)
- **PostgreSQL** — [Descargar PostgreSQL](https://www.postgresql.org/download/)
- **Git** para clonar el repositorio
- Un IDE compatible (IntelliJ IDEA, Eclipse o VS Code)
- *(Opcional, para el flujo de pagos)* La pasarela [`checkeo-service`](https://github.com/Davidaguilar03/checkeo-service) en ejecución

> No es necesario instalar Maven: el proyecto incluye el **Maven Wrapper** (`mvnw` / `mvnw.cmd`).

---

## Configuración de la base de datos

1. Abre tu cliente de PostgreSQL (pgAdmin, DBeaver o `psql`).
2. Crea la base de datos:

   ```sql
   CREATE DATABASE "TicketeoDB";
   ```

3. Verifica las credenciales en `src/main/resources/application.properties` y ajústalas a tu entorno:

   ```properties
   spring.datasource.url=jdbc:postgresql://localhost:5432/TicketeoDB
   spring.datasource.username=postgres   # tu usuario de postgres
   spring.datasource.password=12345      # tu contraseña de postgres
   ```

> La propiedad `spring.jpa.hibernate.ddl-auto=update` permite que Hibernate cree y actualice automáticamente las tablas a partir de las entidades al desplegar la aplicación.

---

## Instalación y ejecución

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/OscarRoa34/Ticketeo.git
   cd Ticketeo
   ```

2. **Compila y ejecuta** con el Maven Wrapper:

   **Linux / macOS:**
   ```bash
   ./mvnw spring-boot:run
   ```
   *(Si falta el permiso de ejecución: `chmod +x mvnw`)*

   **Windows:**
   ```bash
   mvnw.cmd spring-boot:run
   ```

3. **Accede a la aplicación** en el navegador:

   **http://localhost:8080**

---

## Credenciales por defecto

Usuario administrador disponible para pruebas:

| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Contraseña | `admin` |
| Rol | `ADMIN` |

---

## Pruebas y calidad

Ejecuta la suite de pruebas y genera el reporte de cobertura:

```bash
./mvnw test
```

El reporte de JaCoCo se genera en `target/site/jacoco/`. El proyecto está configurado para análisis de calidad con SonarQube y verificación continua mediante GitHub Actions.

---

## Estructura del proyecto

```
Ticketeo/
├── .github/workflows/   # Pipelines de CI/CD (GitHub Actions)
├── docs/                # Documentación
├── src/
│   ├── main/
│   │   ├── java/        # Código fuente (controllers, services, entities, security)
│   │   └── resources/   # application.properties, plantillas Thymeleaf, estáticos
│   └── test/            # Pruebas unitarias, de integración y E2E
├── uploads/             # Recursos cargados
├── pom.xml              # Dependencias y configuración de build
└── mvnw / mvnw.cmd      # Maven Wrapper
```

---

## Autor

Desarrollado por 
[**David Aguilar**](https://github.com/Davidaguilar03) — Ingeniería de Sistemas, UPTC.
[**Oscar Roa**](https://github.com/OscarRoa34) — Ingeniería de Sistemas, UPTC.

