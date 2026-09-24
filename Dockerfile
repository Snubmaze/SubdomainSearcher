FROM python:3.14-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1

FROM base AS development
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
COPY searcher/ ./searcher/
ENTRYPOINT ["python", "-m", "searcher.main"]
