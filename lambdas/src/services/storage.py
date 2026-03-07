import os
import io
import pandas as pd
import logging
import awswrangler as wr
from typing import Optional

class StorageService:
    def __init__(self, bucket_name: str, delta_table_path: str):
        self.bucket = bucket_name
        self.delta_table_path = delta_table_path or ""
        self.is_aws = "s3://" in self.delta_table_path
        
        if self.is_aws:
            import boto3
            self.s3_client = boto3.client('s3')
        else:
            try:
                from azure.storage.blob import BlobServiceClient
                from azure.identity import DefaultAzureCredential
                account_url = f"https://{self.bucket.split('/')[0]}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(account_url, credential=DefaultAzureCredential())
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

    def get_delta_table(self, source_filter: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Reads Gold Zone Parquet files from S3 using AWS Wrangler.
        Allows column pushdown to save memory in the Lambda execution environment.
        """
        try:
            if not self.is_aws:
                # Fallback purely for local/azure testing if needed
                logging.warning("Reading from non-AWS source is not fully optimized for PyArrow parquets.")
                return pd.DataFrame()
            
            # OPTIMIZACIÓN CRÍTICA: Solo cargar columnas para búsqueda directamente desde S3 Parquet
            columns_to_read = ['nombre_original', 'nombre_limpio', 'fuente', 'tipo_lista', 'metadata']
            
            # Using AWS Wrangler to read partitioned Parquet dataset
            logging.info(f"Reading dataset from {self.delta_table_path}")
            
            if source_filter:
                logging.info(f"Applying partition filter for source: {source_filter}")
                df = wr.s3.read_parquet(
                    path=self.delta_table_path,
                    dataset=True,
                    columns=columns_to_read,
                    partition_filter=lambda x: x["fuente"] == source_filter.upper()
                )
            else:
                df = wr.s3.read_parquet(
                    path=self.delta_table_path,
                    dataset=True,
                    columns=columns_to_read
                )
            return df
            
        except Exception as e:
            logging.error(f"Error loading Parquet Dataset from S3: {e}")
            raise e
