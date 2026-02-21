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

## 2. Nivel 2: Diagrama de Contenedores
Detalle de los servicios en Azure y cómo se comunican entre sí.

```mermaid
C4Container
    title Diagrama de Contenedores - Arquitectura Híbrida Azure
    
    Person(user, "Oficial de Cumplimiento", "Realiza consultas")
    
    Boundary(azure_cloud, "Azure Cloud") {
        Container(logic_app, "Azure Logic App", "Recurrence Trigger", "Orquestador que dispara el ETL diariamente.")
        
        Container(azure_func, "Azure Functions (Python)", "FastAPI/Functions", "Motor ETL: Ingesta, Transformación y Carga.")
        
        ContainerDb(adls, "Azure Data Lake Storage Gen2", "Parquet/Delta Lake", "Capa de persistencia Medallón (Bronze, Silver, Gold).")
        
        Container(api_fastapi, "FastAPI Service", "Python 3.10", "API de búsqueda con Fuzzy Matching (WRatio).")
    }

    System_Ext(ext_sources, "Fuentes Externas (OFAC, SAT, ONU)", "Proveedores de datos CSV/XML.")

    Rel(user, api_fastapi, "Consulta nombre", "JSON/HTTPS")
    Rel(logic_app, azure_func, "Dispara pasos ETL", "HTTP/Managed Identity")
    Rel(azure_func, ext_sources, "Descarga datos", "HTTPS")
    Rel(azure_func, adls, "Escribe Bronze/Silver/Gold", "abfss (Delta Protocol)")
    Rel(api_fastapi, adls, "Lee de la capa Gold", "deltalake (delta-rs)")
```

## 3. Flujo de Datos (Arquitectura Medallón)

1.  **Ingesta (Bronze)**: La Azure Function descarga los archivos originales (CSV/XML) y los guarda en Parquet crudo.
2.  **Transformación (Silver)**: Se aplica la lógica de `shared/normalization.py`. Los nombres se limpian (mayúsculas, sin acentos, sin stop words) y se genera un esquema unificado.
3.  **Carga (Gold)**: Se realiza un `MERGE` atómico en una tabla Delta Lake particionada por fuente.
4.  **Consulta**: La API recibe un nombre, lo normaliza y utiliza `rapidfuzz` sobre los datos de la capa Gold para devolver coincidencias con score de confianza.

## 4. Seguridad
- **Autenticación**: Managed Identity (System Assigned).
- **Autorización**: RBAC (Storage Blob Data Contributor/Reader).
- **Secretos**: No se utilizan llaves de acceso en el código ni en configuraciones.
```
