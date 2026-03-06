import os
import boto3
import urllib3
import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def onu_handler(event, context):
    """
    Lightweight Lambda function to download ONU Consolidated list and save to S3 Landing Zone.
    Executed by Step Functions. Requires 256MB RAM.
    """
    s3 = boto3.client('s3')
    http = urllib3.PoolManager()
    try:
        bucket = os.environ['COMPLIANCE_LAKE_BUCKET']
        landing_prefix = "landing/listas/onu"
        url = os.environ.get('ONU_URL', 'https://scsanctions.un.org/resources/xml/en/consolidated.xml')
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        logger.info(f"Downloading ONU data from {url}")
        response = http.request('GET', url)
        
        if response.status != 200:
            raise Exception(f"Failed to download data. HTTP Status: {response.status}")
            
        data = response.data
        logger.info(f"Downloaded {len(data)} bytes of data.")
        
        s3_key = f"{landing_prefix}/fecha_carga={today_str}/consolidated.xml"
        logger.info(f"Uploading raw xml data to s3://{bucket}/{s3_key}")
        
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=data
        )
        
        return {
            "status": "success",
            "source": "onu",
            "landing_path": f"s3://{bucket}/{s3_key}",
            "records_bytes": len(data),
            "date": today_str
        }
        
    except Exception as e:
        logger.error(f"Error extracting ONU data: {str(e)}")
        raise e
