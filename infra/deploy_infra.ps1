# ComplianceGuard Foundation Deployment Script
$ErrorActionPreference = 'Stop'

$STACK_NAME = "reinesdev-compliance-foundation"
$REGION = "us-east-1"

Write-Host "--- DESPLEGANDO CAPA DE FUNDACIÓN (Infraestructura Core) ---" -ForegroundColor Cyan

aws cloudformation deploy `
    --template-file foundation.yaml `
    --stack-name $STACK_NAME `
    --region $REGION `
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM `
    --no-fail-on-empty-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host "Fundación desplegada con éxito." -ForegroundColor Green
    
    # Mostrar recursos creados
    Write-Host "`nRecursos Exportados:"
    aws cloudformation list-exports --region $REGION --query "Exports[?contains(Name, '$STACK_NAME')]" --output table
} else {
    Write-Host "Error en el despliegue de la fundación." -ForegroundColor Red
    exit 1
}
