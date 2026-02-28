# Contexto de Sistema: ComplianceGuard (Estado Actual)

## 1. Estado del Proyecto (Certificado 100%)
El sistema ha alcanzado su madurez productiva en AWS, consolidando una plataforma unificada de cumplimiento con **11 fuentes globales y regionales**.

### Hitos Alcanzados en la Última Sesión:
*   **Fuentes Operativas (11/11):** ONU, OFAC (Clinton), SAT 69B (MEX), FBI, WorldBank, UE, DEA, Interpol, FTO (Terroristas), Contraloría (COL) e IADB (BID).
*   **Ingesta Híbrida:** Uso de **OpenSanctions** como proxy para fuentes bloqueadas por IP en la nube (DEA, Interpol, UE, WorldBank).
*   **Autenticación Socrata:** Integración de API V3 con Basic Auth para la Contraloría de Colombia (Datos Abiertos).
*   **Certificación E2E:** Suite de pruebas `tests/acceptance_e2e_aws.py` validada con **100% de éxito** en AWS Production.

## 2. Arquitectura y Optimización (AWS Lambda)
*   **Memoria:** Escalada a **3008MB** en `template.yaml` para soportar el Data Lake de ~60,000 registros en RAM.
*   **Carga Selectiva:** `StorageService.get_delta_table()` optimizado para cargar solo 5 columnas críticas, reduciendo el consumo de RAM.
*   **API Gateway:** Swagger UI activo en `/prod/docs`. Se añadió filtro por `source` y parámetro `refresh=true` para invalidación de caché.

## 3. Credenciales y Seguridad
*   **Socrata (Colombia):** Credenciales configuradas en `.env` y mapeadas en `Settings` (`DATOS_GOV_KEY_ID`, `DATOS_GOV_API_KEY`).
*   **IAM:** La función de búsqueda ahora tiene `S3CrudPolicy` para permitir la ejecución de los endpoints `/etl/` registrados en el Core.

## 4. Estructura de Datos (Gold Layer)
*   **Esquema Unificado:** `id_unico`, `nombre_original`, `nombre_limpio`, `fuente`, `tipo_lista`, `fecha_carga`, `metadata`.
*   **Particionamiento:** La tabla Delta está particionada por la columna `fuente` para búsquedas eficientes.

## 5. Próximos Pasos (Pendientes)
*   **Azure Finalization:** Portar los cambios de los parsers robustos y la optimización de memoria a la configuración de Azure Functions.
*   **Monitoring:** Implementar alarmas de CloudWatch para detectar fallos en la ingesta diaria de OpenSanctions.
*   **Web UI:** Vincular el archivo `ui/index.html` con el nuevo endpoint `/prod/check/`.

---
**Nota de Contexto:** El motor de búsqueda utiliza `RapidFuzz` con `token_set_ratio`. El umbral recomendado para producción es **85.0**.
