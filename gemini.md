# Contexto de Sistema: ComplianceGuard (Estado Actual)

## 1. Estado del Proyecto (Certificado 100%)
El sistema ha alcanzado su madurez productiva en AWS, consolidando una plataforma unificada de cumplimiento con **11 fuentes globales y regionales**.

### Hitos Alcanzados en la Última Sesión:
*   **Fuentes Operativas (11/11):** ONU, OFAC (Clinton), SAT 69B (MEX), FBI, WorldBank, UE, DEA, Interpol, FTO (Terroristas), Contraloría (COL) e IADB (BID).
*   **Ingesta Híbrida:** Uso de **OpenSanctions** como proxy para fuentes bloqueadas por IP en la nube (DEA, Interpol, UE, WorldBank).
*   **Autenticación Socrata:** Integración de API V3 con Basic Auth para la Contraloría de Colombia (Datos Abiertos).
*   **Certificación E2E:** Suite de pruebas `tests/acceptance_e2e_aws.py` validada con **100% de éxito** en AWS Production.

## 2. Arquitectura y Optimización (AWS ELT)
*   **Orquestación:** Cambio de ETL monolítico a **ELT** utilizando **AWS Step Functions** para procesos paralelos.
*   **Transformación:** Migración completada a **AWS Glue Flex (PySpark)**, reduciendo los costos de computo y superando los límites de memoria de Pandas/DeltaLake.
*   **Almacenamiento:** Transición de DeltaLake a **S3 Parquet Nativo** particionado (`fuente=X`), administrado vía AWS Glue Data Catalog.
*   **Búsqueda (API):** Consumo optimizado con `awswrangler` (Partition Pushdown), bajando la memoria requerida en la Lambda de **3008MB a 1024MB** y Extractoras a **256MB**.
*   **Despliegue API (ECR a ZIP):** Refactorizamos el backend para evitar pesadas imágenes de Docker. Ahora funciona en **Lambda (ZIPs)** gracias al uso de **AWS Managed Layers** (`AWSSDKPandas-Python312`) para inyectar Pandas/awswrangler evadiendo el límite estricto de 250MB de AWS.

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

## 6. Políticas de Repositorio (Git & CI/CD)
Para mantener la limpieza y estabilidad en el despliegue, la próxima sesión de IA deberá adherirse a estas reglas de control de versiones:
*   **Ramas Aisladas:** Todo cambio se desarrolla en ramas descriptivas (`feature/descripción`, `fix/descripción`, `docs/descripción`).
*   **Conventional Commits:** Uso de tipologías (`feat:`, `fix:`, `refactor:`, `docs:`).
*   **Quality Gates:** Un Pull Request debe esperar a que GitHub Actions termine las validaciones de `pytest` (`Test & Quality Gate`) antes de ser fusionado.
*   **Continuous Deployment:** El workflow `deploy-production.yml` orquesta el pase a AWS. Desacopla eficientemente dependencias pesadas de `pip` asumiéndolas dentro de las Layers de AWS.

---
**Nota de Contexto:** El motor de búsqueda utiliza `RapidFuzz` con `token_set_ratio`. El umbral recomendado para producción es **85.0**.
