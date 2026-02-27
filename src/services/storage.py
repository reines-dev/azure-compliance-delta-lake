import os
import io
import pandas as pd
import pyarrow as pa
from typing import Optional
from deltalake import write_deltalake, DeltaTable

class StorageService:
    def __init__(self, bucket_name: str, delta_table_path: str):
        self.bucket = bucket_name
        self.delta_table_path = delta_table_path
        
        # Simple detector for AWS S3 vs Azure Local Storage
        self.is_aws = "s3://" in self.delta_table_path
        
        if self.is_aws:
            import boto3
            self.s3_client = boto3.client('s3')
        else:
            # Azure Data Lake Storage / Blob logic here if needed dynamically
            pass

    def save_parquet(self, df: pd.DataFrame, key: str) -> str:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        
        if self.is_aws:
            self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=buffer.getvalue())
            return f"s3://{self.bucket}/{key}"
        else:
            # Placeholder Azure logic
            return f"abfs://{self.bucket}/{key}"
            
    def read_parquet(self, key: str) -> pd.DataFrame:
        if self.is_aws:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return pd.read_parquet(io.BytesIO(response['Body'].read()))
        else:
            # Placeholder Azure logic
            return pd.DataFrame()

    def save_bronze(self, df: pd.DataFrame, source: str) -> str:
        return self.save_parquet(df, f"bronze/{source}/data.parquet")

    def read_bronze(self, source: str) -> pd.DataFrame:
        return self.read_parquet(f"bronze/{source}/data.parquet")

    def save_silver(self, df: pd.DataFrame, source: str) -> str:
        return self.save_parquet(df, f"silver/{source}/data.parquet")

    def read_silver(self, source: str) -> pd.DataFrame:
        return self.read_parquet(f"silver/{source}/data.parquet")

    def write_gold_delta(self, df: pd.DataFrame, source: str) -> str:
        table = pa.Table.from_pandas(df)
        write_deltalake(
            self.delta_table_path, 
            table, 
            mode="overwrite", 
            partition_by=["fuente"],
            predicate=f"fuente = '{source.upper()}'"
        )
        return self.delta_table_path

    def get_delta_table(self) -> Optional[pd.DataFrame]:
        try:
            dt = DeltaTable(self.delta_table_path)
            return dt.to_pandas()
        except Exception:
            return None
