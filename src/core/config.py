from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Model config
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    # AWS/Azure agnostic config
    compliance_lake_bucket: str = "reinesdev-compliance-lake-prd"
    delta_table_path: str = "s3://reinesdev-compliance-lake-prd/gold/listas"
    enable_docs: bool = True
    
    # Azure Specific (Optional if in AWS)
    azure_storage_connection_string: Optional[str] = None
    storage_account_name: Optional[str] = None
    
    # Sources URLs
    ofac_sdn_url: str = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    ofac_alt_url: str = "https://www.treasury.gov/ofac/downloads/add.csv"
    onu_url: str = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    fbi_wanted_api_url: str = "https://api.fbi.gov/wanted/v1/list"
    worldbank_api_url: str = "https://data.opensanctions.org/datasets/20260228/worldbank_debarred/entities.ftm.json"
    iadb_sancions_url: str = "https://data.iadb.org/api/action/datastore_search?resource_id=cd0bd9ac-18c6-44bc-8592-9be468c2efd9"
    ue_sancions_url: str = "https://data.opensanctions.org/datasets/latest/eu_fsf/entities.ftm.json"
    dea_most_wanted_url: str = "https://data.opensanctions.org/datasets/latest/us_dea_fugitives/entities.ftm.json"
    interpol_red_notices_url: str = "https://data.opensanctions.org/datasets/latest/interpol_red_notices/entities.ftm.json"
    fto_list_url: str = "https://www.state.gov/wp-content/uploads/2023/05/FTO-List-CSV.csv"
    contraloria_url: str = "https://www.datos.gov.co/api/v3/views/jr8e-e8tu/query.json"

@lru_cache()
def get_settings():
    return Settings()
