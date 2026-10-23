FROM python:3.12-slim

WORKDIR /app/all_in_one_orchestration

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/dagster_home
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["sh", "-c", "mkdir -p /app/dagster_home && cd /app/all_in_one_dbt/hf_models && dbt deps --profiles-dir . && dbt parse --profiles-dir . && cd /app/all_in_one_orchestration && dagster dev -h 0.0.0.0 -p 3000"]