# ComplianceGuard: Sistema Híbrido Multi-Cloud de Listas de Control

Este proyecto implementa una solución **arquitectónicamente agnóstica** y escalable para la detección de entidades en listas restrictivas (OFAC, SAT69B, ONU, etc.) utilizando una **Arquitectura Hexagonal (Ports & Adapters)**. El sistema soporta despliegues nativos tanto en **AWS** (Lambda + S3) como en **Azure** (Functions + ADLS Gen2).

## 1. Arquitectura del Sistema (Hexagonal Multi-Cloud)

El sistema separa rigurosamente la lógica de negocio (Core) de la infraestructura específica de la nube (Adapters):

*   **Core Lógico (`src/`)**: 
    *   **FastAPI**: Motor de API neutro que puede correr en cualquier entorno ASGI.
    *   **ETL Flow**: Pipeline agnóstico (Bronze -> Silver -> Gold) basado en `pandas` y `delta-rs`.
*   **Adaptadores de Nube (`cloud/`)**:
    *   **AWS (`cloud/aws/`)**: Implementación para AWS Lambda usando contenedores (ECR), API Gateway y S3. Orquestación vía Step Functions.
    *   **Azure (`cloud/azure/`)**: Implementación para Azure Functions V2, Logic Apps y ADLS Gen2.
*   **Almacenamiento (Delta Lake)**:
    *   Uso de la tabla **Delta Lake** como fuente de verdad única y particionada, permitiendo consultas de milisegundos sin necesidad de clústeres de Spark activos.

## 2. Componentes Técnicos Avanzados

### A. Algoritmo de Búsqueda "Precision-First"
Implementado mediante la librería `rapidfuzz` utilizando el algoritmo **`token_set_ratio`**:
- **Diferenciación Inteligente**: Prioriza registros donde todas las palabras de la consulta están presentes (Score 100), ideal para nombres con apellidos o segundos nombres adicionales.
- **Normalización Agresiva**: Limpia caracteres especiales, acentos y elimina "stop words" corporativas (S.A., SAS, Inc).

### B. Ingesta Multi-Fuente
Centraliza y normaliza automáticamente múltiples listas globales:
1.  **OFAC SDN**: Lista de nacionales especialmente designados (EE. UU.).
2.  **ONU Consolidated**: Lista consolidada del Consejo de Seguridad.
3.  **SAT 69-B (México)**: Listado de empresas facturadoras de operaciones inexistentes.

## 3. Seguridad y Despliegue (Infrastructure as Code)

- **Seguridad**: Basado en el principio de mínimo privilegio. Uso de roles IAM (AWS) e Identidades Administradas (Azure) para acceso al Data Lake sin llaves hardcodeadas.
- **Despliegue AWS**: Automatizado con **AWS SAM** y Docker.
- **Despliegue Azure**: Basado en scripts de PowerShell y plantillas Bicep.

## 4. Estructura del Proyecto

```text
listas_control/
├── src/                # CORE: Lógica agnóstica de negocio y API.
│   ├── api/            # Definiciones de endpoints y esquemas.
│   ├── etl/            # Pipelines de Ingesta, Transformación y Carga.
│   ├── services/       # Abstracciones (StorageService).
│   └── core/           # Configuración global via Pydantic Settings.
├── cloud/              # ADAPTADORES: Código específico de infraestructura.
│   ├── aws/            # Lambda Handlers, SAM Template, Scripts AWS.
│   └── azure/          # Function App, Bicep, Scripts Azure.
├── docker/             # Dockerfiles optimizados para cada nube.
├── tests/              # Pruebas integrales (Unitarias y API).
└── requirements.txt    # Dependencias base del Core.
```

## 5. Pruebas y Validación

- **Unitarias**: `pytest tests/unit` (Lógica de normalización y transformación).
- **Integración**: `pytest tests/integration` (API Gateway / Functions -> Delta Lake).
- **Manuales**: Consultas directas al endpoint `/check/` con API Keys habilitadas.
