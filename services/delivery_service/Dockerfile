FROM dockerhub.timeweb.cloud/library/python:3.13-slim

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PYTHONPATH=/app/services/delivery_service

WORKDIR /app

COPY libs/ ./libs/
RUN pip install --no-cache-dir ./libs

COPY services/delivery_service/requirements.txt ./services/delivery_service/
RUN pip install --no-cache-dir -r ./services/delivery_service/requirements.txt

COPY services/delivery_service/ ./services/delivery_service/

WORKDIR /app/services/delivery_service

CMD ["python", "src/main.py"]
