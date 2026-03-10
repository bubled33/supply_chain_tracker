FROM dockerhub.timeweb.cloud/library/python:3.13-slim

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PYTHONPATH=/app/services/warehouse_service

WORKDIR /app

COPY libs/ ./libs/
RUN pip install --no-cache-dir ./libs

COPY services/warehouse_service/requirements.txt ./services/warehouse_service/
RUN pip install --no-cache-dir -r ./services/warehouse_service/requirements.txt

COPY services/warehouse_service/ ./services/warehouse_service/

WORKDIR /app/services/warehouse_service

CMD ["python", "src/main.py"]
