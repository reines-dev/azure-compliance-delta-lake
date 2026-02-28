# Arquitectura del Sistema - ComplianceGuard

Este documento describe la arquitectura de alta disponibilidad y agnóstica a la nube para el sistema de consulta de listas restrictivas.

## 1. Nivel 1: Diagrama de Contexto
El sistema interactúa con oficiales de cumplimiento y un ecosistema diverso de fuentes internacionales y regionales.

```mermaid
C4Context
    title Diagrama de Contexto - ComplianceGuard
    Person(compliance_officer, "Oficial de Cumplimiento", "Usuario que realiza consultas de nombres.")
    System(compliance_system, "ComplianceGuard", "Gestiona la ingesta de 11+ listas y permite búsquedas difusas.")
    
    System_Ext(opensanctions, "OpenSanctions", "Proxy de datos para DEA, Interpol, UE y WorldBank.")
    System_Ext(ofac, "OFAC / FBI / ONU", "Fuentes directas internacionales.")
    System_Ext(sat, "SAT 69-B México", "Fuente oficial del SAT.")
    System_Ext(datos_gov, "Contraloría Colombia", "API V3 Socrata con Autenticación.")

    Rel(compliance_officer, compliance_system, "Consulta nombres / razones sociales", "HTTPS/REST")
    Rel(compliance_system, opensanctions, "Descarga datasets consolidados", "HTTPS/JSONL")
    Rel(compliance_system, datos_gov, "Consulta responsables fiscales", "HTTPS/API V3 Auth")
    Rel(compliance_system, ofac, "Descarga listas oficiales", "HTTPS/CSV")
```

## 2. Nivel 2: Diagrama de Contenedores (Arquitectura Hexagonal)
Detalle del diseño desacoplado que permite la portabilidad total entre AWS y Azure.

```mermaid
C4Container
    title Arquitectura Hexagonal Multi-Cloud
    
    Person(user, "Usuario / App Externa", "Consultas vía API / Swagger")
    
    Boundary(core, "Núcleo Agnóstico (src/)") {
        Container(fastapi_core, "API FastAPI", "Python 3.12", "Búsqueda Difusa (RapidFuzz), Swagger UI, Filtrado por Fuente.")
        Container(etl_pipeline, "ETL Pipeline", "Python 3.12", "Orquestación Ingesta -> Transformación -> Carga Gold.")
        Container(storage_service, "Storage Service", "Python (delta-rs)", "Abstracción Data Lake con Optimización de Memoria.")
    }

    Boundary(aws_adapter, "Adaptador AWS (Desplegado)") {
        Container(aws_step_func, "Step Functions", "Orquestador", "Flujo Medallón diario automático.")
        Container(aws_lambda, "Lambda (3008MB)", "Compute", "Ejecuta el Core optimizado para +58k registros.")
        Container(aws_s3, "Amazon S3", "Data Lake", "Tablas Delta particionadas por FUENTE.")
    }

    Rel(user, fastapi_core, "GET /check/?name=X&source=Y", "HTTPS")
    Rel(fastapi_core, storage_service, "Consulta optimizada (5 columnas)")
    Rel(etl_pipeline, storage_service, "Escritura ACID con Predicados")
    Rel(storage_service, aws_s3, "delta-rs / S3 SDK")
```

## 3. Flujo de Datos y Optimización

### Estrategia de Ingesta Híbrida
Debido a bloqueos de IP en nubes públicas, el sistema utiliza un enfoque triple:
1.  **Directo:** OFAC, ONU, FBI, FTO y SAT descargados desde servidores oficiales.
2.  **Proxy (OpenSanctions):** DEA, Interpol, UE y WorldBank obtenidos vía datasets estructurados JSONL.
3.  **Autenticado:** Contraloría de Colombia vía API V3 con credenciales de Socrata.

### Rendimiento del Motor de Búsqueda
*   **Volumen:** ~58,500 registros unificados.
*   **Memoria:** Uso de 3GB de RAM en Lambda para mantener el DataFrame de búsqueda en caliente.
*   **Columnas Ligeras:** Solo se cargan 5 campos críticos (`nombre_limpio`, `nombre_original`, `fuente`, `tipo_lista`, `metadata`) para maximizar la velocidad y estabilidad.

## 4. Seguridad y Gobernanza
*   **Identidad:** Acceso a S3 vía IAM Roles (Amazon) y Managed Identity (Azure).
*   **Secretos:** Credenciales de Datos Abiertos inyectadas vía variables de entorno en el despliegue de IaC.
*   **Documentación:** OpenAPI 3.1 / Swagger UI activo para integración simplificada.
