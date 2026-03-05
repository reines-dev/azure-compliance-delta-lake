# ComplianceGuard MCP - Nested Stacks Deployment Script
# Despliega toda la arquitectura modular bajo un único Root Stack.

$ErrorActionPreference = 'Stop'

function Assert-LastCommand {
    param([string]$Message)
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: $Message" -ForegroundColor Red
        exit 1
    }
}

try {
    # 1. Configuración
    $REGION = 'us-east-1'
    $S3_BUCKET = 'hreines-sam-deploy'
    $STACK_NAME = 'reinesdev-compliance-root'
    $REPO_NAME = 'reinesdev-compliance-api-repo'

    $ROOT_DIR = $PSScriptRoot
    if (-not $ROOT_DIR) { $ROOT_DIR = Get-Location }
    Set-Location $ROOT_DIR

    Write-Host "`n=== INICIANDO DESPLIEGUE ATÓMICO (NESTED STACKS) ===" -ForegroundColor Cyan

    # 0. Obtener Identidad y Login ECR
    $ACCOUNT_ID = (aws sts get-caller-identity --query 'Account' --output text)
    Assert-LastCommand 'No se pudo obtener la identidad de AWS.'
    
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
    Assert-LastCommand 'Falló el login en ECR.'

    # 1. Sincronizar scripts Glue (Capa ETL)
    Write-Host '`n[1/4] Sincronizando scripts Glue...' -ForegroundColor Gray
    aws s3 sync glue/jobs/ s3://reinesdev-compliance-lake-prd/system/glue_jobs/ --exclude '*' --include '*.py'

    # 2. Construir y subir imagen Docker (Capa API)
    Write-Host '`n[2/4] Preparando imagen Docker de la API...' -ForegroundColor Gray
    $ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest"
    
    # Crear repo si no existe
    aws ecr describe-repositories --repository-names $REPO_NAME --region $REGION 2>$null
    if ($LASTEXITCODE -ne 0) {
        aws ecr create-repository --repository-name $REPO_NAME --region $REGION
    }

    docker build -t $REPO_NAME -f api/Dockerfile.aws .
    docker tag "${REPO_NAME}:latest" $ECR_URI
    docker push $ECR_URI
    Assert-LastCommand 'Falló el push de la imagen Docker.'

    # 3. CloudFormation Package (Sube templates anidados y código Lambda a S3)
    Write-Host '`n[3/4] Empaquetando arquitectura modular...' -ForegroundColor Gray
    aws cloudformation package `
        --template-file infra/root-template.yaml `
        --s3-bucket $S3_BUCKET `
        --output-template-file infra/packaged-root.yaml
    Assert-LastCommand 'Falló el empaquetado de CloudFormation.'

    # 4. CloudFormation Deploy (Despliegue Atómico)
    Write-Host '`n[4/4] Desplegando Root Stack en AWS...' -ForegroundColor Cyan
    aws cloudformation deploy `
        --template-file infra/packaged-root.yaml `
        --stack-name $STACK_NAME `
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND `
        --parameter-overrides "ImageUri=$ECR_URI" `
        --no-fail-on-empty-changeset
    Assert-LastCommand 'Falló el despliegue del stack principal.'

    Write-Host "`n=== DESPLIEGUE COMPLETADO EXITOSAMENTE ===" -ForegroundColor Green
    $API_URL = aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text
    Write-Host "Endpoint Final: $API_URL" -ForegroundColor Yellow

} catch {
    Write-Host "`n--- ERROR CRÍTICO EN EL DESPLIEGUE ---" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
