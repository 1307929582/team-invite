FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data

EXPOSE 4567

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4567", "--workers", "4"]
