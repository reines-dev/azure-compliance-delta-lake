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
    # PySpark CSV reader does not natively support `skipRows`. We must read without header and find it.
    raw_df = spark.read.option("header", "false") \
        .option("encoding", "latin1") \
        .csv(sat_landing_path)

    def clean_string(name):
        if not name:
            return ""
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().upper()

    clean_string_udf = udf(clean_string, StringType())

    # 3. Transform SAT 69B
    # Check the first 15 rows to find the actual header row dynamically
    sample_rows = raw_df.take(15)
    header_row = None

    for row in sample_rows:
        row_values = [str(x).upper() for x in row if x is not None]
        if any("RFC" in val for val in row_values) and any("NOMBRE" in val for val in row_values):
            header_row = row
            break

    if not header_row:
        logger.error(f"Sample rows evaluated: {sample_rows}")
        raise ValueError("Could not find a valid header row containing RFC and NOMBRE in the SAT CSV.")

    # Map the actual indices
    col_rfc_index = None
    col_nombre_index = None
    col_situacion_index = None

    for idx, val in enumerate(header_row):
        if not val:
            continue
        val_upper = str(val).upper()
        if "RFC" in val_upper:
            col_rfc_index = f"_c{idx}"
        elif "NOMBRE" in val_upper:
            col_nombre_index = f"_c{idx}"
        elif "SITUAC" in val_upper:
            col_situacion_index = f"_c{idx}"

    if not col_rfc_index or not col_nombre_index or not col_situacion_index:
        raise ValueError(f"Missing required columns (RFC, NOMBRE, SITUACION) within the resolved header row: {header_row}")

    # Explicitly filter out the document headers, actual header row, and empty rows
    data_df = raw_df.filter(
        col(col_rfc_index).isNotNull() & 
        (~col(col_rfc_index).rlike("(?i)RFC")) & 
        (~col(col_rfc_index).rlike("(?i)Información"))
    )

    transformed_df = data_df.select(
        md5(concat_ws("-", lit("SAT69B"), col(col_rfc_index))).alias("id_unico"),
        col(col_nombre_index).alias("nombre_original"),
        clean_string_udf(col(col_nombre_index)).alias("nombre_limpio"),
        col(col_rfc_index).alias("identificacion"),
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
