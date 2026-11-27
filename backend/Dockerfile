FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# El contexto de construcción es la raíz del repositorio: docker build -f backend/Dockerfile .
COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install -r requirements.txt -r requirements-ml.txt

COPY backend/ .

# Pronóstico con la TCN (HU-19): código del paquete y modelo entrenado.
# Sin estos archivos el backend usa el promedio móvil de 4 semanas (ADR-0003).
COPY ml/originlink_ml /ml/originlink_ml
COPY ml/models/tcn_global.pt /ml/models/tcn_global.pt
ENV MODEL_PATH=/ml/models/tcn_global.pt \
    ML_PATH=/ml

# Cloud Run define PORT (8080 por defecto).
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
