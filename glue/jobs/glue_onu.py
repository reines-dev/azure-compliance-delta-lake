import sys
import datetime
import re
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, lit, current_date, udf, md5, concat_ws, date_format, explode
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

onu_landing_path = f"{landing_path}/onu/fecha_carga={today_str}/consolidated.xml"

logger = glueContext.get_logger()
logger.info(f"Reading raw data from {onu_landing_path}")

try:
    # 2. Extract Data (ONU XML Format)
    # Requerimos el databricks-xml parsing (soportado en AWS Glue nativamente especificando format="xml")
    raw_df = spark.read.format("xml") \
        .option("rowTag", "INDIVIDUAL") \
        .load(onu_landing_path)

    # Limpiador de cadenas UDF
    def clean_string(name):
        if not name:
            return ""
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().upper()

    clean_string_udf = udf(clean_string, StringType())

    # 3. Transform INDIVIDUALS
    if "DATAID" in raw_df.columns:
        # Extraer nombres. La ONU divide en FIRST_NAME, SECOND_NAME, etc.
        indiv_df = raw_df.select(
            md5(concat_ws("-", lit("ONU"), col("DATAID"))).alias("id_unico"),
            concat_ws(" ", col("FIRST_NAME"), col("SECOND_NAME"), col("THIRD_NAME")).alias("nombre_original"),
            lit("Individuo").alias("tipo_entidad"),
            lit("ONU_CONSOLIDATED").alias("tipo_lista"),
            col("REFERENCE_NUMBER").alias("metadata")
        )
        
        transformed_df = indiv_df.select(
            col("id_unico"),
            col("nombre_original"),
            clean_string_udf(col("nombre_original")).alias("nombre_limpio"),
            lit("-").alias("identificacion"),
            col("tipo_entidad"),
            col("tipo_lista"),
            date_format(current_date(), "yyyy-MM-dd").alias("fecha_carga"),
            lit("ONU").alias("fuente"),
            col("metadata").cast(StringType())
        )
        
        # 4. Load INDIVIDUALS
        logger.info(f"Writing INDIVIDUALS to {gold_path} partitioned by fuente")
        transformed_df.write \
            .mode("append") \
            .partitionBy("fuente") \
            .parquet(f"{gold_path}/")

    # Repeat extraction for ENTITIES (ONU usa INDIVIDUAL y ENTITY tag)
    entity_df = spark.read.format("xml") \
        .option("rowTag", "ENTITY") \
        .load(onu_landing_path)
        
    if "DATAID" in entity_df.columns:
         ent_df = entity_df.select(
            md5(concat_ws("-", lit("ONU"), col("DATAID"))).alias("id_unico"),
            col("FIRST_NAME").alias("nombre_original"), # Las entidades usan a menudo FIRST_NAME para su nombre principal
            lit("Empresa").alias("tipo_entidad"),
            lit("ONU_CONSOLIDATED").alias("tipo_lista"),
            col("REFERENCE_NUMBER").alias("metadata")
         )
         
         transformed_ent = ent_df.select(
            col("id_unico"),
            col("nombre_original"),
            clean_string_udf(col("nombre_original")).alias("nombre_limpio"),
            lit("-").alias("identificacion"),
            col("tipo_entidad"),
            col("tipo_lista"),
            date_format(current_date(), "yyyy-MM-dd").alias("fecha_carga"),
            lit("ONU").alias("fuente"),
            col("metadata").cast(StringType())
         )
         
         logger.info(f"Writing ENTITIES to {gold_path} partitioned by fuente")
         transformed_ent.write \
            .mode("append") \
            .partitionBy("fuente") \
            .parquet(f"{gold_path}/")

    logger.info("Glue ONU ETL Job completed successfully.")
    
except Exception as e:
    logger.error(f"Error processing ONU data: {str(e)}")
    raise e

job.commit()
