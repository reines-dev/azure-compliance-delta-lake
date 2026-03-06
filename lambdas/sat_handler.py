import os
import boto3
import urllib3
import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def sat69b_handler(event, context):
    """
    Lightweight Lambda function to download SAT 69B (Mexico) list and save to S3 Landing Zone.
    Executed by Step Functions. Requires 256MB RAM.
    """
    s3 = boto3.client('s3')
    try:
        bucket = os.environ['COMPLIANCE_LAKE_BUCKET']
        landing_prefix = "landing/listas/sat"
        url = os.environ.get('SAT69B_URL', 'http://omawww.sat.gob.mx/cifras_sat/Documents/ListadoGlobalDefinitivo.csv')
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        logger.info(f"Downloading SAT 69B data from {url}")
        
        # SAT usa HTTP no-seguro a veces y puede bloquear ciertos User-Agents
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = http.request('GET', url, headers=headers)
        
        if response.status != 200:
            raise Exception(f"Failed to download data. HTTP Status: {response.status}")
            
        data = response.data
        logger.info(f"Downloaded {len(data)} bytes of data.")
        
        s3_key = f"{landing_prefix}/fecha_carga={today_str}/definitivo.csv"
        logger.info(f"Uploading raw csv data to s3://{bucket}/{s3_key}")
        
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=data
        )
        
        return {
            "status": "success",
            "source": "sat",
            "landing_path": f"s3://{bucket}/{s3_key}",
            "records_bytes": len(data),
            "date": today_str
        }
        
    except Exception as e:
        logger.error(f"Error extracting SAT 69B data: {str(e)}")
        raise e
