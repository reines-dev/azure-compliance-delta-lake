# Proyecto: Sistema Híbrido de Cumplimiento (Compliance) en Azure

## 1. Estado Actual del Proyecto
El sistema ha sido implementado, validado y documentado siguiendo una arquitectura Medallón sobre Delta Lake. Se han integrado con éxito las fuentes principales (OFAC, ONU, SAT69B) y se ha preparado la infraestructura para listas adicionales (UE, DEA, LPB, IRAQ).

### Componentes Entregados:
*   **ETL Dinámica (Azure Functions):** Localizada en `azure_functions/`. Implementa endpoints dinámicos por fuente (`/ingest/{source}`, `/transform/{source}`, `/load/{source}`).
*   **API de Consulta (FastAPI):** Localizada en `api/`. Realiza búsquedas difusas (Fuzzy Matching) con el algoritmo `WRatio` de `rapidfuzz` sobre la capa Gold del Delta Lake.
*   **Orquestación (Logic App):** Definición en `logic_app/workflow.json` y despliegue automatizado vía Bicep en `infrastructure/logic_app.bicep`.
*   **Automatización de Despliegue:** Script `infrastructure/deploy.ps1` que aprovisiona la infraestructura completa en Azure (Central US) bajo la suscripción `91a951e6-4f42-4b04-b903-453ada37d059`.

## 2. Arquitectura Técnica (Medallón)
1.  **Bronze:** Datos originales descargados (CSV/XML) guardados en Parquet.
2.  **Silver:** Datos normalizados (mayúsculas, sin acentos, sin stop words corporativas) con esquema unificado e ID único (`{id}_{fuente}`).
3.  **Gold (Delta Lake):** Tabla particionada por `fuente` en ADLS Gen2.
    *   **Importante:** Se utiliza el parámetro `predicate` en `write_deltalake` para asegurar actualizaciones atómicas por partición y evitar la sobrescritura total de la tabla.

## 3. Configuración y Seguridad
*   **Seguridad:** Implementación de **Managed Identity** (System Assigned) en Azure. En entorno local (WSL), el motor de Rust (`delta-rs`) requiere las variables `AZURE_STORAGE_ACCOUNT` y `AZURE_STORAGE_KEY` inyectadas en el entorno para autenticación directa.
*   **Variables de Entorno:** Centralizadas en `.env` (API/Tests) y `local.settings.json` (Functions). Obligatorias para evitar valores hardcodeados.

## 4. Pruebas y Validación E2E
Se han realizado pruebas reales con ~40,000 registros:
*   **Normalización:** Valida limpieza de sufijos como "S.A.", "SAS", etc.
*   **Fuzzy Matching:** Validado con casos reales (ej. búsqueda de "Nicolás Maduro" detectando sus registros en la OFAC con score > 90%).
*   **Integración:** Validada la lectura/escritura directa en Azure Storage `listasdeltalake` desde WSL.

## 5. Roadmap / Pendientes
*   **Finalizar Publicación de Código:** Ejecutar `func azure functionapp publish` y `az webapp up` tras estabilizar las cuotas de Azure.
*   **Fuentes Adicionales:** Configurar URLs reales para UE, DEA y LPB en las variables de entorno para activar su ingesta automática.
*   **Monitoreo:** Configurar alertas en Application Insights para fallos en el proceso de transformación.

---
**Contexto de Sistema:** Entorno Windows con WSL (Ubuntu), Python 3.10/3.12, .venv activo en subcarpetas.
