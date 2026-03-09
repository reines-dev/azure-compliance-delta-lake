import sys
import datetime
import uuid
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

landing_path = args.get('LANDING_ZONE_PATH')
gold_path = args.get('GOLD_ZONE_PATH')

if not landing_path or not gold_path:
    raise ValueError("LANDING_ZONE_PATH y GOLD_ZONE_PATH originados de la Step Function son obligatorios.")

today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

# Full path to today's raw file
ofac_landing_path = f"{landing_path}/ofac/fecha_carga={today_str}/sdn.csv"
logger = glueContext.get_logger()
logger.info(f"Reading raw data from {ofac_landing_path}")

# 2. Extract: Read CSV from Landing Zone
# OFAC CSV has specific columns (often without header, we infer or specify manually, 
# but for robust parser we assume standard OFAC columns)
raw_df = spark.read.option("header", "false").csv(ofac_landing_path)

# OFAC usually has:
# _c0: ent_num (ID)
# _c1: SDN_Name
# _c2: SDN_Type (individual, entity, vessel)
# _c3: Programs
# _c4: Title
# _c5: Call_Sign
# _c6: Vess_type
# _c7: Tonnage
# _c8: GRT
# _c9: Vess_flag
# _c10: Vess_owner
# _c11: Remarks

# Filter out empty rows just in case
raw_df = raw_df.filter(col("_c1").isNotNull() & (col("_c1") != ""))

# 3. Transform: Data Cleansing using Spark Functions
# Define a UDF to clean names (similar to existing logic)
def clean_string(name):
    if not name:
        return ""
    # Remove special chars, lowercase, trim
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip().upper()

clean_string_udf = udf(clean_string, StringType())

# Generate standardized schema
transformed_df = raw_df.select(
    # Unico ID generation: hash of source + ent_num to prevent collisions globally
    md5(concat_ws("-", lit("OFAC"), col("_c0"))).alias("id_unico"),
    
    col("_c1").alias("nombre_original"),
    clean_string_udf(col("_c1")).alias("nombre_limpio"),
    
    lit("-").alias("identificacion"), # Sometimes OFAC contains passports in Remarks, but typically needs deep parse.
    col("_c2").alias("tipo_entidad"),
    lit("OFAC_SDN").alias("tipo_lista"),
    
    date_format(current_date(), "yyyy-MM-dd").alias("fecha_carga"),
    lit("OFAC").alias("fuente"),
    
    # Store remaining data as metadata (in JSON format ideally or concatenated)
    concat_ws(" | ", col("_c3"), col("_c11")).alias("metadata")
)

# Replace empty strings in `identificacion` or `tipo_entidad` with standard nulls/dashes
transformed_df = transformed_df.fillna("-", subset=["identificacion", "tipo_entidad"])

# 4. Load: Write to S3 Gold Zone in Parquet, partitioned by source
logger.info(f"Writing transformed data to {gold_path} partitioned by fuente")

transformed_df.write \
    .mode("overwrite") \
    .partitionBy("fuente") \
    .parquet(f"{gold_path}/")

logger.info("Glue OFAC ETL Job completed successfully.")
job.commit()
