FROM dockerhub.timeweb.cloud/library/python:3.13-slim

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PYTHONPATH=/app/services/auth_service

WORKDIR /app

COPY libs/ ./libs/
RUN pip install --no-cache-dir ./libs

COPY services/auth_service/requirements.txt ./services/auth_service/
RUN pip install --no-cache-dir -r ./services/auth_service/requirements.txt

COPY services/auth_service/ ./services/auth_service/

WORKDIR /app/services/auth_service

CMD ["python", "src/main.py"]
