# Stage 1: Oracle Instant Client 19c (x86_64)
FROM --platform=linux/amd64 ghcr.io/oracle/oraclelinux8-instantclient:19 AS oracle-instant
#FROM ghcr.io/oracle/oraclelinux8-instantclient:19 AS oracle-instant

# Stage 2: Python 3.13-slim container for application
FROM --platform=linux/amd64 python:3.13-slim
#FROM python:3.13-slim

# 1) Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        libaio1 \
        libnsl-dev \
        ghostscript \
    && rm -rf /var/lib/apt/lists/*

# 2) Create target directory for Oracle client
RUN mkdir -p /opt/oracle/instantclient

# 3) Set Oracle environment variables
ENV APP_ENV=qa
ENV ORACLE_HOME=/opt/oracle/instantclient
ENV LD_LIBRARY_PATH=$ORACLE_HOME
ENV PATH=$ORACLE_HOME:$PATH

# 4) Copy Oracle Instant Client - SOLUCIÓN DEFINITIVA
COPY --from=oracle-instant /usr/lib/oracle/19.*/client64/* $ORACLE_HOME/

# 6) Set working directory
WORKDIR /app

# 7) Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 8) Copy application code
COPY . .

# 8.1) Precompile Python bytecode
RUN python -m compileall /app

# 9) Expose application port
EXPOSE 8000

# 10) Default command to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]