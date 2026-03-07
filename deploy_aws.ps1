# ComplianceGuard App Deployment Script
$ErrorActionPreference = 'Stop'

try {
    $REGION = 'us-east-1'
    $FOUNDATION_STACK = 'reinesdev-compliance-foundation'
    $APP_STACK = 'reinesdev-compliance-root'
    # Configuración de Artefactos de SAM
    # PRIORIDAD: Variable de Entorno > Valor por Defecto
    $SAM_BUCKET = $env:SAM_DEPLOY_BUCKET
    if (-not $SAM_BUCKET) {
        $SAM_BUCKET = 'hreines-sam-deploy' # Valor por defecto (Cambiar si es necesario)
    }

    Write-Host "Obteniendo recursos de la fundación..." -ForegroundColor Cyan
    $stack = aws cloudformation describe-stacks --stack-name $FOUNDATION_STACK --region $REGION --output json | ConvertFrom-Json
    $COMPLIANCE_BUCKET = ($stack.Stacks[0].Outputs | Where-Object { $_.OutputKey -eq "BucketName" }).OutputValue
    $ECR_URI = ($stack.Stacks[0].Outputs | Where-Object { $_.OutputKey -eq "EcrRepoUri" }).OutputValue

    Write-Host "Target Bucket: $COMPLIANCE_BUCKET"
    Write-Host "Target ECR: $ECR_URI"

    # Login ECR
    $ACCOUNT_ID = (aws sts get-caller-identity --query 'Account' --output text)
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

    # 1. Sync Glue Scripts
    Write-Host "Sincronizando scripts de Glue..."
    aws s3 sync glue/jobs/ "s3://${COMPLIANCE_BUCKET}/system/glue_jobs/" --exclude '*' --include '*.py'

    # 2. Package Lambdas
    Write-Host "Empaquetando Lambdas..."
    $ZIP_NAME = "extractors.zip"
    if (Test-Path $ZIP_NAME) { Remove-Item $ZIP_NAME -Force }
    if (Test-Path "lambdas/src") { Remove-Item "lambdas/src" -Recurse -Force }
    Copy-Item "src" "lambdas/src" -Recurse
    Compress-Archive -Path "lambdas/*" -DestinationPath "./$ZIP_NAME" -Force
    Remove-Item "lambdas/src" -Recurse -Force

    # 3. Build & Push API Docker
    Write-Host "Construyendo imagen de API..."
    docker build -t compliance-api -f src/api/Dockerfile.aws .
    docker tag "compliance-api:latest" "${ECR_URI}:latest"
    docker push "${ECR_URI}:latest"

    # 4. Package CloudFormation
    Write-Host "Empaquetando CloudFormation..."
    aws cloudformation package `
        --template-file infra/root-template.yaml `
        --s3-bucket $SAM_BUCKET `
        --output-template-file packaged-root.yaml

    # 5. Deploy App Stack
    Write-Host "Desplegando Stack de Aplicación..."
    aws cloudformation deploy `
        --template-file packaged-root.yaml `
        --stack-name $APP_STACK `
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND `
        --parameter-overrides "FoundationStackName=$FOUNDATION_STACK" "ImageUri=${ECR_URI}:latest" `
        --no-fail-on-empty-changeset

    Write-Host "Despliegue de aplicación completado con éxito." -ForegroundColor Green

} catch {
    Write-Host "Error en el despliegue: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    if (Test-Path "lambdas/src") { Remove-Item "lambdas/src" -Recurse -Force }
}
