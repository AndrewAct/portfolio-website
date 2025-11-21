FROM python:3.11-alpine

WORKDIR /app

COPY services/history /app

# Copy shared files (configs, logs, ...)
COPY shared /app/shared

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
