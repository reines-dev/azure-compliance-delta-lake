from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # AWS/Azure agnostic config
    compliance_lake_bucket: str
    delta_table_path: str
    
    # Sources URLs
    ofac_sdn_url: str
    ofac_alt_url: str
    sat69b_url: str
    onu_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    return Settings()
