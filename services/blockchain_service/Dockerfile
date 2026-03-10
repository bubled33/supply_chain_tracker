FROM dockerhub.timeweb.cloud/library/python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends gcc libssl-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PYTHONPATH=/app/services/blockchain_service

WORKDIR /app

COPY libs/ ./libs/
RUN pip install --no-cache-dir ./libs

COPY services/blockchain_service/requirements.txt ./services/blockchain_service/
RUN pip install --no-cache-dir -r ./services/blockchain_service/requirements.txt

COPY services/blockchain_service/ ./services/blockchain_service/

WORKDIR /app/services/blockchain_service

CMD ["python", "src/main.py"]
