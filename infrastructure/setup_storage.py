import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

def setup_storage():
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        print("❌ Error: AZURE_STORAGE_CONNECTION_STRING no definida.")
        return

    try:
        service = BlobServiceClient.from_connection_string(conn_str)
        container_name = "datalake"
        
        # Intentar crear el contenedor
        try:
            service.create_container(container_name)
            print(f"✅ Contenedor '{container_name}' creado con éxito.")
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                print(f"ℹ️ El contenedor '{container_name}' ya existe.")
            else:
                print(f"⚠️ Error al crear contenedor: {e}")
                
    except Exception as e:
        print(f"❌ Error de conexión al Storage: {e}")

if __name__ == "__main__":
    setup_storage()
