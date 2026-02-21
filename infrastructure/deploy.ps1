<#
.SYNOPSIS
    Script de despliegue optimizado para Central US con Plan B1 compartido.
#>

$ErrorActionPreference = "Stop"

$SubscriptionId = "91a951e6-4f42-4b04-b903-453ada37d059"
Write-Host "Estableciendo suscripcion activa: $SubscriptionId" -ForegroundColor Cyan
az account set --subscription $SubscriptionId

# --- RECURSOS EXISTENTES ---
$ResourceGroup = "cumplimiento-deltalake"
$StorageName = "listasdeltalake"
$Location = "centralus" # Region validada con cuota B1
$ContainerName = "datalake"

# --- NUEVOS RECURSOS ---
$Suffix = (Get-Random -Minimum 1000 -Maximum 9999)
$AppServicePlan = "asp-listas-compliance-$Suffix"
$FunctionAppName = "func-etl-listas-$Suffix"
$WebAppName = "api-listas-search-$Suffix"
$LogicAppName = "logic-listas-orchestrator-$Suffix"

Write-Host "=== INICIANDO DESPLIEGUE EN $Location ===" -ForegroundColor Cyan

# 1. Crear App Service Plan B1 (Validado con cuota)
Write-Host "`n[1/6] Creando App Service Plan B1..." -ForegroundColor Yellow
az appservice plan create --name $AppServicePlan --resource-group $ResourceGroup --location $Location --sku B1 --is-linux -o table

# 2. Crear Azure Function (En el Plan B1 compartido)
Write-Host "`n[2/6] Creando Azure Function..." -ForegroundColor Yellow
az functionapp create --name $FunctionAppName --storage-account $StorageName --plan $AppServicePlan --resource-group $ResourceGroup --runtime python --runtime-version 3.10 --functions-version 4 --os-type linux --assign-identity -o table

# 3. Crear Web App (API) en el mismo Plan B1
Write-Host "`n[3/6] Creando Web App para API..." -ForegroundColor Yellow
az webapp create --name $WebAppName --resource-group $ResourceGroup --plan $AppServicePlan --runtime "PYTHON:3.10" --assign-identity -o table
az webapp config set --name $WebAppName --resource-group $ResourceGroup --startup-file "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000" -o table

# 4. Configurar Permisos RBAC (Managed Identity)
Write-Host "`n[4/6] Asignando Roles RBAC..." -ForegroundColor Yellow
$FuncPrincipalId = az functionapp identity show --name $FunctionAppName --resource-group $ResourceGroup --query principalId --output tsv
$WebPrincipalId = az webapp identity show --name $WebAppName --resource-group $ResourceGroup --query principalId --output tsv
$StorageId = az storage account show --name $StorageName --resource-group $ResourceGroup --query id --output tsv

az role assignment create --assignee $FuncPrincipalId --role "Storage Blob Data Contributor" --scope $StorageId -o table
az role assignment create --assignee $WebPrincipalId --role "Storage Blob Data Reader" --scope $StorageId -o table

# 5. Configurar App Settings
Write-Host "`n[5/6] Configurando App Settings..." -ForegroundColor Yellow
$StorageUrl = "https://$StorageName.blob.core.windows.net/"
$DeltaPath = "abfss://$ContainerName@$StorageName.dfs.core.windows.net/tables/listas_restrictivas"
$BasePath = "abfss://$ContainerName@$StorageName.dfs.core.windows.net/"

$Settings = "STORAGE_ACCOUNT_URL=$StorageUrl DELTA_TABLE_PATH=$DeltaPath BASE_STORAGE_PATH=$BasePath SCM_DO_BUILD_DURING_DEPLOYMENT=true DEFAULT_SEARCH_THRESHOLD=85.0 DEFAULT_SEARCH_LIMIT=5 OFAC_SDN_URL=https://www.treasury.gov/ofac/downloads/sdn.csv OFAC_ALT_URL=https://www.treasury.gov/ofac/downloads/alt.csv SAT69B_URL=http://omawww.sat.gob.mx/cifras_fiscales/Tablas/Listado_Completo_69-B.csv SAT69B_ENCODING=latin-1"

az functionapp config appsettings set --name $FunctionAppName --resource-group $ResourceGroup --settings $Settings -o table
az webapp config appsettings set --name $WebAppName --resource-group $ResourceGroup --settings $Settings -o table

# 6. Desplegar Logic App (Bicep)
# Nota: Si el registro de Microsoft.Logic falla, este paso se puede omitir y hacer manual
Write-Host "`n[6/6] Desplegando Logic App (Bicep)..." -ForegroundColor Yellow
try {
    $LogicPrincipalId = az deployment group create --resource-group $ResourceGroup --template-file "infrastructure/logic_app.bicep" --parameters logicAppName=$LogicAppName functionAppName=$FunctionAppName --query properties.outputs.logicAppPrincipalId.value --output tsv
    az role assignment create --assignee $LogicPrincipalId --role "Website Contributor" --scope "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionAppName" -o table
} catch {
    Write-Host "Advertencia: El despliegue de la Logic App fallo (posible falta de registro de Microsoft.Logic). Por favor crear manualmente si es necesario." -ForegroundColor Red
}

Write-Host "`n=== INFRAESTRUCTURA LISTA ===" -ForegroundColor Green
Write-Host "Function App: $FunctionAppName"
Write-Host "Web App API: $WebAppName"
Write-Host "`nEjecuta esto para subir el codigo:"
Write-Host "func azure functionapp publish $FunctionAppName --python"
Write-Host "az webapp up --name $WebAppName --resource-group $ResourceGroup --runtime PYTHON:3.10"
