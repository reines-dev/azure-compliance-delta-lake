import os
import json
import boto3
import urllib3
import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def ofac_handler(event, context):
    """
    Lightweight Lambda function to download OFAC SDN list and save to S3 Landing Zone.
    Executed by Step Functions. Requires 256MB RAM.
    """
    s3 = boto3.client('s3')
    http = urllib3.PoolManager()
    try:
        # 1. Configuration
        bucket = os.environ['COMPLIANCE_LAKE_BUCKET']
        landing_prefix = "landing/listas/ofac"
        url = os.environ.get('OFAC_SDN_URL', 'https://www.treasury.gov/ofac/downloads/sdn.csv')
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        # 2. Extract (Download)
        logger.info(f"Downloading OFAC data from {url}")
        response = http.request('GET', url)
        
        if response.status != 200:
            raise Exception(f"Failed to download data. HTTP Status: {response.status}")
            
        data = response.data
        logger.info(f"Downloaded {len(data)} bytes of data.")
        
        # 3. Load to Landing Zone (Raw)
        s3_key = f"{landing_prefix}/fecha_carga={today_str}/sdn.csv"
        logger.info(f"Uploading raw data to s3://{bucket}/{s3_key}")
        
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=data
        )
        
        logger.info("Upload complete.")
        
        # Return success payload for Step Functions
        return {
            "status": "success",
            "source": "ofac",
            "landing_path": f"s3://{bucket}/{s3_key}",
            "records_bytes": len(data),
            "date": today_str
        }
        
    except Exception as e:
        logger.error(f"Error extracting OFAC data: {str(e)}")
        raise e
