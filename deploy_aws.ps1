# ComplianceGuard Deployment Script
$ErrorActionPreference = 'Stop'

try {
    $REGION = 'us-east-1'
    $S3_BUCKET = 'hreines-sam-deploy'
    $STACK_NAME = 'reinesdev-compliance-root'
    $REPO_NAME = 'reinesdev-compliance-api-repo'

    Write-Host "Iniciando despliegue..."

    $ACCOUNT_ID = (aws sts get-caller-identity --query 'Account' --output text)
    
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

    # Glue
    aws s3 sync glue/jobs/ s3://reinesdev-compliance-lake-prd/system/glue_jobs/ --exclude '*' --include '*.py'

    # Preparar Lambdas
    if (Test-Path "lambdas/src") { Remove-Item "lambdas/src" -Recurse -Force }
    Copy-Item "src" "lambdas/src" -Recurse

    # API Docker
    $ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest"
    docker build -t $REPO_NAME -f src/api/Dockerfile.aws .
    docker tag "${REPO_NAME}:latest" $ECR_URI
    docker push $ECR_URI

    # Package
    aws cloudformation package --template-file infra/root-template.yaml --s3-bucket $S3_BUCKET --output-template-file packaged-root.yaml

    # Deploy
    aws cloudformation deploy --template-file packaged-root.yaml --stack-name $STACK_NAME --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --parameter-overrides "ImageUri=$ECR_URI" --no-fail-on-empty-changeset

    Write-Host "Despliegue completado con éxito."

} catch {
    Write-Host "Error en el despliegue: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path "lambdas/src") { Remove-Item "lambdas/src" -Recurse -Force }
}
