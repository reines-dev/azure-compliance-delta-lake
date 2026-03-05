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

sat_landing_path = f"{landing_path}/sat/fecha_carga={today_str}/definitivo.csv"

logger = glueContext.get_logger()
logger.info(f"Reading raw SAT 69B data from {sat_landing_path}")

try:
    # 2. Extract Data (SAT CSV Format)
    raw_df = spark.read.option("header", "true").option("encoding", "latin1").csv(sat_landing_path)

    def clean_string(name):
        if not name:
            return ""
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().upper()

    clean_string_udf = udf(clean_string, StringType())

    # 3. Transform SAT 69B
    # Columnas principales en SAT suelen ser "RFC" y "Nombre del Contribuyente" "Situación del contribuyente"
    col_rfc = [c for c in raw_df.columns if "RFC" in c.upper()][0]
    col_nombre = [c for c in raw_df.columns if "NOMBRE" in c.upper()][0]
    col_situacion = [c for c in raw_df.columns if "SITUAC" in c.upper()][0]

    transformed_df = raw_df.select(
        md5(concat_ws("-", lit("SAT69B"), col(col_rfc))).alias("id_unico"),
        col(col_nombre).alias("nombre_original"),
        clean_string_udf(col(col_nombre)).alias("nombre_limpio"),
        col(col_rfc).alias("identificacion"),
        lit("Empresa").alias("tipo_entidad"),
        lit("SAT69B_RESTRICTIVA").alias("tipo_lista"),
        date_format(current_date(), "yyyy-MM-dd").alias("fecha_carga"),
        lit("SAT69B").alias("fuente"),
        concat_ws(" | Situación: ", col(col_situacion)).alias("metadata")
    )

    transformed_df = transformed_df.fillna("-", subset=["identificacion", "tipo_entidad"])

    # 4. Load to Gold Zone
    logger.info(f"Writing SAT 69B Data to {gold_path} partitioned by fuente")
    transformed_df.write \
        .mode("overwrite") \
        .partitionBy("fuente") \
        .parquet(f"{gold_path}/")

    logger.info("Glue SAT 69B ETL Job completed successfully.")

except Exception as e:
    logger.error(f"Error processing SAT 69B data: {str(e)}")
    raise e

job.commit()
