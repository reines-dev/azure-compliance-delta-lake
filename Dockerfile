# AWS Glue 4.0 usa Python 3.10 y Spark 3.3.0
# Usamos la imagen oficial de AWS que ya trae configurado Spark, Hadoop y los Jars de awsglue
FROM amazon/aws-glue-libs:glue_libs_4.0.0_image_01

# El usuario por defecto en esta imagen es 'glue_user'
USER root

# Actualizar e instalar dependencias del sistema si es necesario
RUN yum install -y gcc gcc-c++ && yum clean all

# Cambiar al directorio de trabajo estándar de la imagen
WORKDIR /home/glue_user/workspace

# Copiar el código fuente
COPY ./src ./src
COPY ./tests ./tests
COPY ./glue/jobs ./glue_jobs
COPY requirements-test.txt .

# Instalar los requerimientos de Python del proyecto
RUN pip3 install --upgrade pip && \
  pip3 install -r requirements-test.txt && \
  pip3 install pytest pytest-cov

# Dar permisos al usuario de glue
RUN chown -R glue_user /home/glue_user/workspace

USER glue_user

# Comando por defecto (puedes sobrescribirlo para correr pytest o un job en particular)
# Ejemplo para correr pruebas: CMD ["python3", "-m", "pytest", "tests/"]
CMD ["/bin/bash"]
