import os
import boto3
import urllib3
import datetime
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def opensanctions_proxy_handler(event, context):
    """
    Generic Lambda function to download OpenSanctions data sets (UE, Interpol, FBI, etc.)
    Expected event payload: {"source_id": "fbi_wanted"}
    Executed by Step Functions. Requires 256MB RAM.
    """
    s3 = boto3.client('s3')
    http = urllib3.PoolManager()
    try:
        source_id = event.get('source_id')
        if not source_id:
            raise ValueError("El parámetro 'source_id' no está definido en el payload del evento.")
        
        bucket = os.environ['COMPLIANCE_LAKE_BUCKET']
        landing_prefix = f"landing/listas/opensanctions/{source_id}"
        
        # Generar endpoint dinamico de OpenSanctions
        url = f"https://data.opensanctions.org/datasets/latest/{source_id}/entities.ftm.json"
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        logger.info(f"Downloading OpenSanctions data for {source_id} from {url}")
        response = http.request('GET', url)
        
        if response.status != 200:
            raise Exception(f"Failed to download data. HTTP Status: {response.status}")
            
        data = response.data
        logger.info(f"Downloaded {len(data)} bytes of data.")
        
        s3_key = f"{landing_prefix}/fecha_carga={today_str}/entities.json"
        logger.info(f"Uploading raw json data to s3://{bucket}/{s3_key}")
        
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=data
        )
        
        return {
            "status": "success",
            "source": source_id,
            "landing_path": f"s3://{bucket}/{s3_key}",
            "records_bytes": len(data),
            "date": today_str
        }
        
    except Exception as e:
        logger.error(f"Error extracting OpenSanctions data: {str(e)}")
        raise e
