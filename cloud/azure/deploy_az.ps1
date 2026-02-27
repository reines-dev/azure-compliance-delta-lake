<#
.SYNOPSIS
    Script de despliegue optimizado para Central US con Plan B1 compartido.
    ComplianceGuard MCP - Arquitectura Hexagonal Azure Functions V2.
#>

$ErrorActionPreference = "Stop"

$SubscriptionId = "91a951e6-4f42-4b04-b903-453ada37d059"
Write-Host "Estableciendo suscripcion activa: $SubscriptionId" -ForegroundColor Cyan
az account set --subscription $SubscriptionId

# --- NUEVOS NOMBRES (Naming Convention reinesdev-compliance) ---
$ResourceGroup = "reinesdev-compliance-rg-prd"
$StorageName = "reinesdevcomplakeprd" # Limite 24 caracteres, sin guiones
$Location = "centralus" # Region validada con cuota B1
$ContainerName = "gold"

$AppServicePlan = "reinesdev-compliance-asp-prd"
$FunctionAppName = "reinesdev-compliance-func-prd"

Write-Host "=== INICIANDO DESPLIEGUE EN $Location ===" -ForegroundColor Cyan

# 1. Crear Grupo de Recursos y Storage Account si no existen
Write-Host "`n[1/5] Creando Base de Infraestructura..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location -o table
az storage account create --name $StorageName --resource-group $ResourceGroup --location $Location --sku Standard_LRS --enable-hierarchical-namespace true -o table
az storage container create --account-name $StorageName --name $ContainerName --auth-mode login -o table

# 2. Crear App Service Plan B1 (Validado con cuota)
Write-Host "`n[2/5] Creando App Service Plan..." -ForegroundColor Yellow
az appservice plan create --name $AppServicePlan --resource-group $ResourceGroup --location $Location --sku B1 --is-linux -o table

# 3. Crear Azure Function (Envolvendo FastAPI y ETL)
Write-Host "`n[3/5] Creando Azure Function V2 (Python 3.12)..." -ForegroundColor Yellow
az functionapp create --name $FunctionAppName --storage-account $StorageName --plan $AppServicePlan --resource-group $ResourceGroup --runtime python --runtime-version 3.12 --functions-version 4 --os-type linux --assign-identity -o table

# 4. Configurar Permisos RBAC (Managed Identity)
Write-Host "`n[4/5] Asignando Roles RBAC (Storage Blob Data Contributor)..." -ForegroundColor Yellow
$FuncPrincipalId = az functionapp identity show --name $FunctionAppName --resource-group $ResourceGroup --query principalId --output tsv
$StorageId = az storage account show --name $StorageName --resource-group $ResourceGroup --query id --output tsv

az role assignment create --assignee $FuncPrincipalId --role "Storage Blob Data Contributor" --scope $StorageId -o table

# 5. Configurar App Settings
Write-Host "`n[5/5] Configurando App Settings..." -ForegroundColor Yellow
$DeltaPath = "abfss://$ContainerName@$StorageName.dfs.core.windows.net/listas"

# Configuracion base para el codigo agnostico y los adaptadores V2
$Settings = "COMPLIANCE_LAKE_BUCKET=$StorageName DELTA_TABLE_PATH=$DeltaPath SCM_DO_BUILD_DURING_DEPLOYMENT=true OFAC_SDN_URL=https://www.treasury.gov/ofac/downloads/sdn.csv OFAC_ALT_URL=https://www.treasury.gov/ofac/downloads/add.csv ONU_URL=https://scsanctions.un.org/resources/xml/en/consolidated.xml SAT69B_URL=https://www.sat.gob.mx/listas_69B.csv"

az functionapp config appsettings set --name $FunctionAppName --resource-group $ResourceGroup --settings $Settings -o table

Write-Host "`n=== INFRAESTRUCTURA LISTA ===" -ForegroundColor Green
Write-Host "Function App (API & ETL): $FunctionAppName"
Write-Host "`nEjecuta los siguientes comandos para subir el codigo a Azure:"
Write-Host "cd cloud/azure"
Write-Host "func azure functionapp publish $FunctionAppName --python"
