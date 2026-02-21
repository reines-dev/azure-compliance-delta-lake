# Sistema de Detección de Entidades Restringidas (Compliance Architecture)

Este proyecto implementa una solución híbrida escalable en **Azure** para la detección de entidades en listas restrictivas (OFAC, SAT69B, ONU, etc.) utilizando una arquitectura de datos moderna y servicios de bajo costo.

## 1. Arquitectura del Sistema (Híbrida)

El sistema sigue el patrón de **Arquitectura Medallón** para garantizar la calidad y trazabilidad de los datos:

*   **Capa ETL (Ingesta y Transformación)**:
    *   **Azure Logic Apps**: Orquestador que dispara el proceso diariamente (10:00 AM).
    *   **Azure Functions (Python)**: Realiza la descarga (Ingesta), limpieza (Transformación) y carga final (Merge/Upsert) en el Data Lake.
*   **Capa de Almacenamiento (Delta Lake)**:
    *   **Azure Data Lake Storage (ADLS Gen2)**: Almacena los datos en tres etapas:
        *   **Bronze**: Datos crudos en formato Parquet (ofac_raw, sat69b_raw).
        *   **Silver**: Datos normalizados y con esquema unificado (id_unico, nombre_limpio, fuente).
        *   **Gold**: Tabla **Delta Lake** optimizada para consultas de alta velocidad.
*   **Capa de API (Consulta)**:
    *   **FastAPI**: Servicio RESTful que lee directamente del Delta Lake (usando `delta-rs`) sin necesidad de clústeres de Spark activos (optimización de costos).

## 2. Componentes Técnicos

### A. Normalización de Nombres (`shared/normalization.py`)
Algoritmo centralizado que asegura que tanto las cargas como las consultas utilicen el mismo estándar:
- Conversión a mayúsculas y eliminación de acentos (Unicodedata).
- Limpieza de caracteres especiales y números no relevantes.
- Eliminación de **Stop Words Corporativas** (S.A., SAS, LLC, INC, CORP, LTDA, etc.).

### B. Búsqueda Difusa (Fuzzy Matching)
Implementada en la API mediante la librería `rapidfuzz` (algoritmo `WRatio`), permitiendo detectar:
- Variaciones ortográficas.
- Cambios en el orden de los nombres (ej: "SANTOS JUAN" vs "JUAN SANTOS").
- Omisiones parciales.

### C. Fuentes de Datos Soportadas
1.  **OFAC SDN List**: Lista de nacionales especialmente designados (EE. UU.).
2.  **SAT 69-B (México)**: Lista de contribuyentes con operaciones inexistentes (facturadoras).

## 3. Seguridad y Permisos (Managed Identity)

El sistema elimina el uso de secretos y llaves estáticas mediante el uso de **Identidades Administradas**:

- **Azure Function**: Tiene el rol `Storage Blob Data Contributor` sobre el ADLS Gen2.
- **API (Web App)**: Tiene el rol `Storage Blob Data Reader` sobre el ADLS Gen2.
- **Logic App**: Tiene el rol `Website Contributor` para invocar la Azure Function de forma segura.

## 4. Configuración y Variables de Entorno

Toda la configuración se realiza mediante variables de entorno (App Settings):

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `BASE_STORAGE_PATH` | Ruta raíz del contenedor en ADLS | `abfss://datalake@account.dfs.../` |
| `DELTA_TABLE_PATH` | Ruta a la tabla Delta final (Gold) | `abfss://datalake@account.dfs.../tables/listas` |
| `DEFAULT_SEARCH_THRESHOLD` | Score mínimo para hallazgos (0-100) | `85.0` |
| `DEFAULT_SEARCH_LIMIT` | Máximo de resultados por consulta | `5` |
| `OFAC_SDN_URL` | URL de descarga de la lista OFAC | `https://www.treasury.gov/...` |
| `SAT69B_URL` | URL de descarga de la lista SAT | `http://omawww.sat.gob.mx/...` |

## 5. Guía de Despliegue

### Requisitos:
- Azure CLI y Azure Functions Core Tools.
- PowerShell 7+.

### Pasos:
1.  **Infraestructura**: Ejecutar `.\infrastructure\deploy.ps1`. Este script crea todos los recursos en la suscripción `91a951e6-4f42-4b04-b903-453ada37d059`.
2.  **Código**:
    - Subir Function: `func azure functionapp publish <Nombre_Func> --python`.
    - Subir API: `az webapp up --name <Nombre_API> --resource-group <RG> --runtime PYTHON:3.10`.

## 6. Estructura del Proyecto

```text
listas_control/
├── api/                # Aplicación FastAPI y servicios de consulta.
├── azure_functions/    # Ingesta, Transformación y Carga (Medallón).
├── shared/             # Lógica compartida (Normalización).
├── tests/              # Pruebas Unitarias e Integración (Pytest).
├── infrastructure/     # Bicep, Scripts de Despliegue y Seguridad.
├── logic_app/          # Definición del Workflow de orquestación.
└── requirements.txt    # Dependencias de Python.
```

## 7. Pruebas y Validación

- **Unitarias**: `pytest tests/unit` (Valida lógica de negocio sin conexión).
- **Integración**: `pytest tests/integration` (Valida API -> Delta Lake).
- **Manuales**: Ejecutar `python test_api.py` para simular búsquedas reales de entidades.
