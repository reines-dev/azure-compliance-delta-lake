# ComplianceGuard MCP - AWS Deployment Script (ELT Architecture)
# Este script sube los jobs de AWS Glue y despliega la infraestructura en AWS.

$STACK_NAME = "reinesdev-compliance-prd"
$REGION = "us-east-1"
$LAKE_BUCKET_NAME = "reinesdev-compliance-lake-prd"
$SAM_BUCKET = "hreines-sam-deploy" # Bucket para los assets de CloudFormation

# Asegurar que estamos en la raíz del proyecto
$SCRIPT_PATH = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Get-Item "$SCRIPT_PATH\..\.."
Set-Location $ROOT_DIR.FullName

Write-Host "--- Iniciando Despliegue de ComplianceGuard ELT ---" -ForegroundColor Cyan
Write-Host "Directorio de trabajo: $((Get-Location).Path)"

# 1. Sincronizar scripts de PySpark hacia la zona de sistema del Data Lake
Write-Host "[1/3] Sincronizando scripts PySpark (AWS Glue) hacia S3..."
aws s3 sync src/glue_jobs/ s3://$LAKE_BUCKET_NAME/system/glue_jobs/ --exclude "*" --include "*.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló la subida de los scripts Glue a S3." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Build con SAM
Write-Host "[2/3] Construyendo paquete de despliegue SAM..."
sam build --template cloud/aws/template.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló la construcción SAM." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 3. Deploy
Write-Host "[3/3] Desplegando orquestación en AWS CloudFormation..."
sam deploy `
    --stack-name $STACK_NAME `
    --region $REGION `
    --s3-bucket $SAM_BUCKET `
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND `
    --no-confirm-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host "--- Despliegue ELT Completado Exitosamente ---" -ForegroundColor Green
    $API_URL = aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text --no-cli-pager
    Write-Host "API Gateway (FastAPI) URL: $API_URL" -ForegroundColor Yellow
    Write-Host "Nota: AWS Step Functions y Glue están listos para orquestar la ingesta en S3." -ForegroundColor Yellow
}
else {
    Write-Host "--- Error en el Despliegue ---" -ForegroundColor Red
}
