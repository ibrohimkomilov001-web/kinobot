# Kino Makoni backend — production image.
#
# DIQQAT: bitta worker (--workers 1, entrypoint.sh'ga qarang). Telegram MTProto
# sessiya fayli (TG_SESSION_DIR, VOLUME /data) bir nechta jarayon orasida
# ULASHILMAYDI — ko'p worker sessiyani buzib qo'yishi yoki Telegram tomonidan
# bloklanishga olib kelishi mumkin.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts
COPY alembic.ini entrypoint.sh ./

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data \
    && chmod +x entrypoint.sh

VOLUME ["/data"]
EXPOSE 8000

USER appuser

ENTRYPOINT ["./entrypoint.sh"]
