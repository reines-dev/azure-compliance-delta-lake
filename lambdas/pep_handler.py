import os
import boto3
import urllib3
import datetime
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def socrata_pep_handler(event, context):
    """
    Lightweight Lambda function to download PEP (Colombia) list from Socrata and save to S3 Landing Zone.
    Executed by Step Functions. Requires 256MB RAM.
    """
    s3 = boto3.client('s3')
    http = urllib3.PoolManager()
    try:
        bucket = os.environ['COMPLIANCE_LAKE_BUCKET']
        landing_prefix = "landing/listas/pep"
        url = os.environ.get('PEP_URL', 'https://www.datos.gov.co/api/v3/views/3qxn-uc22/query.json')
        key_id = os.environ.get('DATOS_GOV_KEY_ID')
        api_key = os.environ.get('DATOS_GOV_API_KEY')
        
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        logger.info(f"Downloading PEP Socrata data from {url}")
        
        # Socrata API V3 suele requerir Basic Auth (Key ID : API Key)
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json'
        }
        
        if key_id and api_key:
            import base64
            auth_str = f"{key_id}:{api_key}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            headers['Authorization'] = f"Basic {encoded_auth}"
            logger.info("Using Basic Auth for Socrata.")
            
        # Intentar peticiÃ³n POST vacÃ­a (estÃ¡ndar en API V3 query) o GET
        response = http.request('POST', url, headers=headers, body=json.dumps({}))
        
        if response.status != 200:
            logger.warning(f"POST failed with {response.status}, trying GET...")
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
