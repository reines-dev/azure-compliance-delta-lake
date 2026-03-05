# ComplianceGuard MCP - AWS Deployment Script (ELT Architecture)
# Este script activa el entorno virtual, sube los jobs de AWS Glue y despliega la infraestructura.

# Detener la ejecución inmediatamente si ocurre un error
$ErrorActionPreference = "Stop"

try {
    # 1. Configuración de Variables
    $STACK_NAME = "reinesdev-compliance-prd"
    $REGION = "us-east-1"
    $LAKE_BUCKET_NAME = "reinesdev-compliance-lake-prd"
    $SAM_BUCKET = "hreines-sam-deploy"

    # 2. Navegar a la raíz del proyecto usando $PSScriptRoot (más confiable)
    $CURRENT_SCRIPT_DIR = $PSScriptRoot
    if (-not $CURRENT_SCRIPT_DIR) { $CURRENT_SCRIPT_DIR = "." }
    $ROOT_DIR = (Get-Item "$CURRENT_SCRIPT_DIR\..\..").FullName
    Set-Location $ROOT_DIR

    Write-Host "`n--- Iniciando Despliegue de ComplianceGuard ELT ---" -ForegroundColor Cyan
    Write-Host "Directorio de trabajo: $ROOT_DIR"

    # 3. Activar entorno virtual local (.venv) si no está activo
    if (-not $env:VIRTUAL_ENV) {
        if (Test-Path ".venv\Scripts\Activate.ps1") {
            Write-Host "[0/3] Activando entorno virtual (.venv)..." -ForegroundColor Gray
            . .venv\Scripts\Activate.ps1
        } elseif (Test-Path ".venv\bin\Activate.ps1") {
            Write-Host "[0/3] Activando entorno virtual (.venv)..." -ForegroundColor Gray
            . .venv\bin\Activate.ps1
        } else {
            Write-Host "ADVERTENCIA: No se encontró .venv. Se usará el Python del sistema." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[0/3] Entorno virtual ya activo ($env:VIRTUAL_ENV)" -ForegroundColor Gray
    }

    # 4. Sincronizar scripts de PySpark hacia la zona de sistema del Data Lake
    Write-Host "[1/3] Sincronizando scripts PySpark (AWS Glue) hacia S3..."
    aws s3 sync src/glue_jobs/ s3://$LAKE_BUCKET_NAME/system/glue_jobs/ --exclude "*" --include "*.py"

    # 5. Build con SAM (Usando contenedores para asegurar compatibilidad con Python 3.12)
    Write-Host "[2/3] Construyendo paquete de despliegue SAM (usando Docker)..."
    sam build --template template.yaml --use-container

    # 6. Deploy
    Write-Host "[3/3] Desplegando infraestructura en AWS..."
    sam deploy `
        --stack-name $STACK_NAME `
        --region $REGION `
        --s3-bucket $SAM_BUCKET `
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND `
        --no-confirm-changeset `
        --resolve-image-repos

    Write-Host "`n--- Despliegue ELT Completado Exitosamente ---" -ForegroundColor Green
    $API_URL = aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text --no-cli-pager
    Write-Host "API Gateway (FastAPI) URL: $API_URL" -ForegroundColor Yellow

} catch {
    Write-Host "`n--- Error Crítico en el Despliegue ---" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
