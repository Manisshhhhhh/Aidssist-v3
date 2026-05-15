FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AIDSSIST_DATABASE_URL=sqlite:////data/aidssist.db \
    AIDSSIST_STORAGE_BACKEND=local \
    AIDSSIST_STORAGE_LOCAL_ROOT=/data/datasets \
    AIDSSIST_REPORTS_LOCAL_ROOT=/data/reports \
    AIDSSIST_DATASETS_DIR=/data/datasets \
    AIDSSIST_REPORTS_DIR=/data/reports

WORKDIR /app

RUN addgroup --system aidssist && \
    adduser --system --ingroup aidssist aidssist && \
    mkdir -p /data/datasets /data/reports && \
    chown -R aidssist:aidssist /data /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts

USER aidssist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
