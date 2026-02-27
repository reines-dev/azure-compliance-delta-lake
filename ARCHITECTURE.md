# Arquitectura del Sistema - C4 Model

Este documento describe la arquitectura del sistema de consulta de listas restrictivas utilizando el modelo C4.

## 1. Nivel 1: Diagrama de Contexto
El sistema interactúa con los oficiales de cumplimiento y fuentes de datos gubernamentales externas.

```mermaid
C4Context
    title Diagrama de Contexto - Sistema de Listas Restrictivas
    Person(compliance_officer, "Oficial de Cumplimiento", "Usuario que realiza consultas de nombres.")
    System(compliance_system, "Sistema de Listas de Control", "Gestiona la ingesta de listas y permite búsquedas difusas.")
    
    System_Ext(ofac, "OFAC / SDN", "Fuente externa de sanciones de EE.UU.")
    System_Ext(sat, "SAT 69-B", "Fuente externa de contribuyentes restringidos en México.")
    System_Ext(un, "ONU", "Lista consolidada de sanciones de Naciones Unidas.")

    Rel(compliance_officer, compliance_system, "Consulta nombres / razones sociales", "HTTPS/REST")
    Rel(compliance_system, ofac, "Descarga listas", "HTTPS")
    Rel(compliance_system, sat, "Descarga listas", "HTTP")
    Rel(compliance_system, un, "Descarga listas", "HTTPS")
```

## 2. Nivel 2: Diagrama de Contenedores (Arquitectura Hexagonal Multi-Cloud)
Detalle de la arquitectura agnóstica que soporta despliegues nativos tanto en AWS como en Azure usando adaptadores.

```mermaid
C4Container
    title Diagrama de Contenedores - Arquitectura Hexagonal Multi-Cloud
    
    Person(user, "Oficial de Cumplimiento", "Realiza consultas vía API")
    
    Boundary(cloud_agnostic_core, "Núcleo Agnóstico (src/)") {
        Container(fastapi_core, "FastAPI Application", "Python 3.12", "Lógica de negocio, Búsqueda Difusa (RapidFuzz), Endpoints REST Puros.")
        Container(etl_pipeline, "ETL Pipeline", "Python 3.12", "Lógica de Ingesta, Transformación y Carga.")
        Container(storage_service, "Storage Service", "Python (delta-rs)", "Abstracción de operaciones Data Lake.")
    }

    Boundary(cloud_adapters, "Adaptadores Nube (cloud/)") {
        Boundary(aws_cloud, "AWS") {
            Container(aws_step_func, "Step Functions", "Orquestador ETL", "Dispara Lambda ETL diariamente.")
            Container(aws_api_gw, "API Gateway", "Proxy", "Enruta tráfico HTTP a la Lambda API.")
            Container(aws_lambda, "AWS Lambda", "Mangum Wrapper", "Ejecuta el núcleo FastAPI y ETL.")
        }
        Boundary(azure_cloud, "Azure") {
            Container(az_logic_app, "Logic App", "Orquestador ETL", "Dispara Function ETL diariamente.")
            Container(az_function, "Azure Function V2", "AsgiFunctionApp Wrapper", "Ejecuta el núcleo FastAPI y ETL.")
        }
    }

    ContainerDb(data_lake, "Data Lake (S3 / ADLS Gen2)", "Parquet / Delta Lake", "Persistencia Medallón (Bronze, Silver, Gold).")
    System_Ext(ext_sources, "Fuentes (OFAC, SAT, ONU)", "Proveedores de Listas Restrictivas.")

    Rel(user, aws_api_gw, "Consulta (Si en AWS)", "HTTPS")
    Rel(user, az_function, "Consulta (Si en Azure)", "HTTPS")
    
    Rel(aws_api_gw, aws_lambda, "Invoca")
    Rel(aws_lambda, fastapi_core, "Envuelve aplicación")
    
    Rel(az_function, fastapi_core, "Envuelve aplicación")

    Rel(aws_step_func, aws_lambda, "Dispara ETL")
    Rel(az_logic_app, az_function, "Dispara ETL")

    Rel(etl_pipeline, ext_sources, "Descarga listas", "HTTPS")
    Rel(storage_service, data_lake, "Aplica MERGE y Consulta Delta", "delta-rs / SDK")
    
    Rel(fastapi_core, storage_service, "Inyecta dependencia de lectura")
    Rel(etl_pipeline, storage_service, "Inyecta dependencia de escritura")
```

## 3. Flujo de Datos (Arquitectura Medallón)

El almacenamiento subyacente depende de la nube desplegada (S3 para AWS o Blob Storage / ADLS Gen2 para Azure), pero el flujo permanece constante gracias a `delta-rs`.

1.  **Ingesta (Bronze)**: El servicio descarga los archivos originales (CSV/XML) mapeados inyectados por la infraestructura, y los guarda en parquet.
2.  **Transformación (Silver)**: Los nombres se limpian (mayúsculas, sin acentos, sin stop words) utilizando `src.etl.normalization` y se genera un esquema unificado con `id_fuente`.
3.  **Carga (Gold)**: Mediante el `StorageService` se aplica un `MERGE` atómico en una tabla Delta Lake única, particionada por fuente.
4.  **Consulta**: `src/api/v1/search.py` (FastAPI) recibe las peticiones, cruza los datos con la capa Gold en memoria parcial usando `rapidfuzz` para coincidencias de alta confiabilidad.

## 4. Nomenclatura, Seguridad y Despliegues

- **Seguridad y Permisos**:  
  Completamente delegados a la nube mediante Roles y Managed Identities asociadas a la política de mínimo privilegio (`Storage Blob Data Contributor/Reader` y roles equivalentes de S3 IAM).  
- **Inyección de Dependencias**: 
  Las URLs origen y nombres físicos de bucket/storage no están hardcodeadas, se inyectan como variables de entorno (usando `pydantic-settings` en `src/core/config.py`) desde el **IaC** (AWS SAM Template o local.settings.json en Azure).
- **Convención Naming**: 
  Cualquier despliegue debe llamarse: `reinesdev-[app]-[recurso]-[entorno]`. Ej: `reinesdev-compliance-api-prd`.
