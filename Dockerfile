FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --gid "$APP_GID" app && useradd --uid "$APP_UID" --gid "$APP_GID" --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir -p /app/data \
    && chown -R app:app /app

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
COPY content ./content
COPY .env.example ./

RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["./scripts/dev.sh"]
