# Configuración de Seguridad y Permisos (Azure)

Para que el sistema funcione de forma segura con **Managed Identity (DefaultAzureCredential)**, se deben seguir estos pasos en el portal de Azure o vía Azure CLI:

## 1. Habilitar Managed Identity
- **Azure Function:** Ir a *Identity* -> *System assigned* -> *On*.
- **Azure Container App / App Service (API):** Ir a *Identity* -> *System assigned* -> *On*.

## 2. Asignación de Roles (RBAC)
Se deben asignar los siguientes roles sobre el **Storage Account** (ADLS Gen2):

| Recurso | Identidad | Rol | Propósito |
|---------|-----------|-----|-----------|
| Storage Account | Azure Function | **Storage Blob Data Contributor** | Para realizar MERGE/Write en la tabla Delta. |
| Storage Account | API (FastAPI) | **Storage Blob Data Reader** | Para leer la tabla Delta y realizar consultas. |

### Comando Azure CLI (Ejemplo):
```bash
# Asignar rol a la Azure Function
az role assignment create 
    --assignee <principal-id-de-la-function> 
    --role "Storage Blob Data Contributor" 
    --scope "/subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.Storage/storageAccounts/<st-name>"

# Asignar rol a la API
az role assignment create 
    --assignee <principal-id-de-la-api> 
    --role "Storage Blob Data Reader" 
    --scope "/subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.Storage/storageAccounts/<st-name>"
```

## 3. Configuración de Variables de Entorno
Asegúrate de configurar estas variables tanto en la Function como en la API:
- `STORAGE_ACCOUNT_URL`: `https://<cuenta>.blob.core.windows.net/`
- `DELTA_TABLE_PATH`: `abfss://<container>@<cuenta>.dfs.core.windows.net/tables/listas_restrictivas`
