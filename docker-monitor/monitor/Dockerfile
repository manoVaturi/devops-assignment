FROM python:3.12-slim

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_DEBUG=0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

# non-root
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app
USER app

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/')" || exit 1

# access log shows the X-Source-IP header as src=<ip>
CMD ["gunicorn", "app:app", \
    "--bind", "0.0.0.0:5000", \
    "--workers", "2", \
    "--access-logfile", "-", \
    "--access-logformat", "%(h)s %(r)s %(s)s src=%({x-source-ip}i)s"]
