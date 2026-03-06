import os
import boto3
import urllib3
import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def socrata_pep_handler(event, context):
    """
    Lightweight Lambda function to download PEP (Colombia) list from Socrata and save to S3 Landing Zone.
    Executed by Step Functions. Requires 256MB RAM.
    """
    s3 = boto3.client('s3')
    try:
        bucket = os.environ['COMPLIANCE_LAKE_BUCKET']
        landing_prefix = "landing/listas/pep"
        url = os.environ.get('PEP_URL', 'https://www.datos.gov.co/api/v3/views/3qxn-uc22/query.json')
        app_token = os.environ.get('DATOS_GOV_API_KEY')
        
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        logger.info(f"Downloading PEP Socrata data from {url}")
        
        headers = {}
        if app_token:
            headers['X-App-Token'] = app_token
            
        response = http.request('GET', url, headers=headers)
        
        if response.status != 200:
            raise Exception(f"Failed to download data. HTTP Status: {response.status}")
            
        data = response.data
        logger.info(f"Downloaded {len(data)} bytes of data.")
        
        s3_key = f"{landing_prefix}/fecha_carga={today_str}/pep_colombia.json"
        logger.info(f"Uploading raw json data to s3://{bucket}/{s3_key}")
        
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=data
        )
        
        return {
            "status": "success",
            "source": "pep",
            "landing_path": f"s3://{bucket}/{s3_key}",
            "records_bytes": len(data),
            "date": today_str
        }
        
    except Exception as e:
        logger.error(f"Error extracting Socrata PEP data: {str(e)}")
        raise e
