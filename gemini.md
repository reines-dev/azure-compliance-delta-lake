# Proyecto: Sistema Híbrido Multi-Cloud (ComplianceGuard)

## 1. Estado Actual del Proyecto
El sistema ha migrado de una implementación monolítica en Azure a una **Arquitectura Hexagonal (Agnóstica a la Nube)** construida sobre FastAPI y Delta Lake. Ahora cuenta con soporte nativo y despliegue cruzado tanto para **AWS (API Gateway + Lambdas + StepFunctions)** como para **Azure (Function App V2 + Logic Apps)**.

### Componentes Entregados:
*   **Núcleo FastAPI (`src/`):** Contiene la lógica profunda ETL (Medallón), modelos Pydantic globales (`schemas.py`, `config.py`) y Endpoints puramente funcionales libres de vendor lock-in (`src/api/v1/search.py`).
*   **Adaptadores Cloud e Infraestructura (`cloud/`):** La antigua carpeta `infrastructure/` fue subsumida aquí.
    *   **AWS (`cloud/aws/`):** Envoltura `Mangum` para API Gateway, IaC con `AWS SAM` (`template.yaml`), y el script de CI/CD automatizado `deploy_aws.ps1`. La orquestación completa corre en **Step Functions**.
    *   **Azure (`cloud/azure/`):** Envoltura `AsgiFunctionApp` para Azure Functions V2, recursos de `logic_app.bicep` y su respectivo script de despliegue `deploy_az.ps1`.
*   **Almacenamiento Genérico:** El puente `StorageService` en `src/services/` abstrae comandos directos de `delta-rs` y `Boto3` (AWS) / Blob SDK (Azure).

## 2. Nomenclatura Estricta (Convención)
Toda la infraestructura cloud ha sido renombrada respetando la directiva de arquitectura elegida.
*   **Estructura Base:** `reinesdev-[nombre_app]-[recurso]-[entorno]`
*   **Ejemplos Reales:** `reinesdev-compliance-api-prd` (API AWS), `reinesdevcomplakeprd` (Storage en Azure).

## 3. Arquitectura Técnica (Medallón)
1.  **Bronze:** Datos originales descargados (CSVs/XML) listos en Parquet.
2.  **Silver:** Datos normalizados (uso de `rapidfuzz` y limpieza de caracteres) con identificadores compuestos `id_fuente`.
3.  **Gold (Delta Lake):** Particionado atómico vía `predicate` sobre los *Data Lakes* (S3Bucket o Blob Storage). 

## 4. Pruebas y Validación (Pytest)
*   **Suite Unitaria (`tests/unit`):** Validando lógica fina sobre Transformación y Normalización en el Core. (8/8 Exitosa).
*   **Suite de Integración:** Uso de `fastapi.testclient.TestClient` emulando las llamadas REST al EndPoint `/check`.

## 5. Roadmap / Pendientes
*   **Orquestación en Azure:** Implementar o portar los manifiestos JSON a ARM/Bicep completos para igualar el `template.yaml` de AWS ya validado.
*   **Despliegue GitHub Actions:** Finalizar rutinas CI/CD combinando los `Dockerfile.aws` / `Dockerfile.azure` optimizados para ambas nubes en flujos de empaque.
*   **Alarma CloudWatch/Insights:** Requisitar permisos `logs:FilterLogEvents` para consolidar trazabilidad.

---
**Contexto de Sistema:** Framework FastAPI, `delta-rs`, Python 3.12 Serverless Apps.
