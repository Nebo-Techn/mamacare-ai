FROM python:3.11-slim


ENV  PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


WORKDIR /app

COPY requirements.txt /app/requirements.txt


RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt


COPY . /app

EXPOSE 8000

ENV HF_TOKEN=""
ENV FAISS_PATH=/app/faiss_local
ENV PYTHONPATH=/app

RUN mkdir -p /app/faiss_local /app/data

CMD [ "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]