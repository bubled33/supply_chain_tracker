FROM dockerhub.timeweb.cloud/library/python:3.13-slim

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PYTHONPATH=/app/services/saga_coordinator

WORKDIR /app

COPY libs/ ./libs/
RUN pip install --no-cache-dir ./libs

COPY services/saga_coordinator/requirements.txt ./services/saga_coordinator/
RUN pip install --no-cache-dir -r ./services/saga_coordinator/requirements.txt

COPY services/saga_coordinator/ ./services/saga_coordinator/

WORKDIR /app/services/saga_coordinator

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
