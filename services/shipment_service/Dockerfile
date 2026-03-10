FROM dockerhub.timeweb.cloud/library/python:3.13-slim

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PYTHONPATH=/app/services/shipment_service

WORKDIR /app

COPY libs/ ./libs/
RUN pip install --no-cache-dir ./libs

COPY services/shipment_service/requirements.txt ./services/shipment_service/
RUN pip install --no-cache-dir -r ./services/shipment_service/requirements.txt

COPY services/shipment_service/ ./services/shipment_service/

WORKDIR /app/services/shipment_service

CMD ["python", "src/main.py"]
