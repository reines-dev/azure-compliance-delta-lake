# ComplianceGuard MCP - AWS Deployment Script (Container Based)
# Este script construye las imágenes de Docker y las despliega en AWS Lambda.

$STACK_NAME = "reinesdev-compliance-prd"
$REGION = "us-east-1"
$LAKE_BUCKET_NAME = "reinesdev-compliance-lake-prd"
$DEPLOY_BUCKET = "hreines-sam-deploy" # Usar el bucket existente que validamos antes

# Asegurar que estamos en la raíz del proyecto
$SCRIPT_PATH = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Get-Item "$SCRIPT_PATH\..\.."
Set-Location $ROOT_DIR.FullName

Write-Host "--- Iniciando Despliegue de ComplianceGuard MCP (Contenedores) ---" -ForegroundColor Cyan
Write-Host "Directorio de trabajo: $((Get-Location).Path)"

# 1. Build con SAM
Write-Host "[1/2] Construyendo imágenes de contenedor..."
sam build --use-container --template cloud/aws/template.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló la construcción de las imágenes." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Deploy
Write-Host "[2/2] Desplegando en AWS..."
# Usamos solo --resolve-image-repos para que SAM gestione ECR automáticamente
sam deploy `
    --stack-name $STACK_NAME `
    --region $REGION `
    --s3-bucket $DEPLOY_BUCKET `
    --resolve-image-repos `
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND `
    --parameter-overrides ComplianceBucketName=$LAKE_BUCKET_NAME `
    --no-confirm-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host "--- Despliegue Completado Exitosamente ---" -ForegroundColor Green
    $API_URL = aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text --no-cli-pager
    Write-Host "API Gateway URL: $API_URL" -ForegroundColor Yellow
}
else {
    Write-Host "--- Error en el Despliegue ---" -ForegroundColor Red
}
