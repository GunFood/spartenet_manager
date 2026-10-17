FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir /data \
    && chown app:app /data

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY --chown=app:app . /app

USER app

EXPOSE 8765

# Docker prüft alle 60 s, ob der Manager antwortet (öffentliche Statusseite, ohne Anmeldung)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('SPARTENET_PORT','8765')+'/status',timeout=8)" || exit 1

CMD ["python", "SparteNet_Manager.py"]
