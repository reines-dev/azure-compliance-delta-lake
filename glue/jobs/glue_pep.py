import sys
import datetime
import re
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, lit, current_date, udf, md5, concat_ws, date_format
from pyspark.sql.types import StringType

# 1. Job Initialization
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'LANDING_ZONE_PATH', 'GOLD_ZONE_PATH'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

landing_path = args.get('LANDING_ZONE_PATH', 's3://reinesdev-compliance-lake-prd/landing/listas')
gold_path = args.get('GOLD_ZONE_PATH', 's3://reinesdev-compliance-lake-prd/gold/listas')
today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

pep_landing_path = f"{landing_path}/pep/fecha_carga={today_str}/pep_colombia.json"

logger = glueContext.get_logger()
logger.info(f"Reading raw data from {pep_landing_path}")

try:
    # 2. Extract Data (Socrata JSON Format)
    raw_df = spark.read.json(pep_landing_path)

    def clean_string(name):
        if not name:
            return ""
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().upper()

    clean_string_udf = udf(clean_string, StringType())

    # 3. Transform Socrata JSON
    # Confirmed Socrata datos.gov.co PEP API v3 schema (2026):
    # nombre_pep, numero_documento, denominacion_cargo, nombre_entidad,
    # fecha_vinculacion, fecha_desvinculacion, enlace_hoja_vida_sigep
    
    logger.info(f"Columns in raw data: {raw_df.columns}")
    
    # Validate expected columns exist
    expected_cols = ["nombre_pep", "numero_documento"]
    missing_cols = [c for c in expected_cols if c not in raw_df.columns]
    if missing_cols:
        logger.warn(f"Missing expected columns: {missing_cols}. Available: {raw_df.columns}")
    else:
        transformed_df = raw_df.select(
            md5(concat_ws("-", lit("PEP"), col("numero_documento"))).alias("id_unico"),
            col("nombre_pep").alias("nombre_original"),
            clean_string_udf(col("nombre_pep")).alias("nombre_limpio"),
            col("numero_documento").alias("identificacion"),
            col("nombre_entidad").alias("tipo_entidad"),
            lit("PEP_COLOMBIA").alias("tipo_lista"),
            date_format(current_date(), "yyyy-MM-dd").alias("fecha_carga"),
            lit("PEP").alias("fuente"),
            concat_ws(" | Cargo: ", col("denominacion_cargo"), col("nombre_entidad")).alias("metadata")
        )
        
        transformed_df = transformed_df.fillna("-", subset=["identificacion", "tipo_entidad"])
        
        # 4. Load PEP to Gold Zone
        logger.info(f"Writing {transformed_df.count()} PEP records to {gold_path}")
        transformed_df.write \
            .mode("overwrite") \
            .partitionBy("fuente") \
            .parquet(f"{gold_path}/")
            
        logger.info("Glue PEP ETL Job completed successfully.")
    
except Exception as e:
    logger.error(f"Error processing Socrata PEP data: {str(e)}")
    raise e

job.commit()
