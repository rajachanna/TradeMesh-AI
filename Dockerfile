FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
RUN useradd -m trader && mkdir -p /data && chown trader:trader /data
USER trader
EXPOSE 8000
CMD ["uvicorn", "trademesh.api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
