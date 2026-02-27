from mangum import Mangum
from src.main import app

# Adaptador ASGI para que API Gateway envíe las peticiones a FastAPI
handler = Mangum(app)
