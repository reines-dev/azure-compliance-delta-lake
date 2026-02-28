import os
import io
import pandas as pd
import pyarrow as pa
import logging
from typing import Optional
from deltalake import write_deltalake, DeltaTable

class StorageService:
    def __init__(self, bucket_name: str, delta_table_path: str):
        self.bucket = bucket_name
        self.delta_table_path = delta_table_path or ""
        self.is_aws = "s3://" in self.delta_table_path
        self.storage_options = {}
        
        if self.is_aws:
            import boto3
            self.s3_client = boto3.client('s3')
            self.storage_options = {"AWS_S3_ALLOW_UNSAFE_RENAME": "true"}
        else:
            try:
                from azure.storage.blob import BlobServiceClient
                from azure.identity import DefaultAzureCredential
                account_url = f"https://{self.bucket.split('/')[0]}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(account_url, credential=DefaultAzureCredential())
                self.storage_options = {"azure_storage_use_managed_identity": "true"}
            except Exception:
                pass

    def _get_clean_bucket(self):
        return self.bucket.replace("s3://", "").split("/")[0]

    def save_parquet(self, df: pd.DataFrame, key: str) -> str:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        if self.is_aws:
            bucket_name = self._get_clean_bucket()
            self.s3_client.put_object(Bucket=bucket_name, Key=key, Body=buffer.getvalue())
            return f"s3://{bucket_name}/{key}"
        return ""
            
    def read_parquet(self, key: str) -> pd.DataFrame:
        if self.is_aws:
            bucket_name = self._get_clean_bucket()
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            return pd.read_parquet(io.BytesIO(response['Body'].read()))
        return pd.DataFrame()

    def write_gold_delta(self, df: pd.DataFrame, source: str) -> str:
        df = df.copy()
        for col in ['id_unico', 'nombre_original', 'nombre_limpio', 'fuente', 'tipo_lista', 'metadata']:
            if col in df.columns:
                df[col] = df[col].astype(str)
        table = pa.Table.from_pandas(df)
        write_deltalake(self.delta_table_path, table, mode="overwrite", partition_by=["fuente"], predicate=f"fuente = '{source.upper()}'", storage_options=self.storage_options, schema_mode="merge")
        return self.delta_table_path

    def get_delta_table(self) -> Optional[pd.DataFrame]:
        try:
            # OPTIMIZACIÓN CRÍTICA: Solo cargar columnas para búsqueda
            dt = DeltaTable(self.delta_table_path, storage_options=self.storage_options)
            return dt.to_pandas(columns=['nombre_original', 'nombre_limpio', 'fuente', 'tipo_lista', 'metadata'])
        except Exception as e:
            logging.error(f"Error loading Delta Table: {e}")
            raise e
