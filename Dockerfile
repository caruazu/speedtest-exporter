FROM python:3.11-slim AS builder

    # evita cache do pip
ENV PIP_NO_CACHE_DIR=1 \ 
    # corta checagem de versão do pip
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # reduz ruído do Pipenv no build
    PIPENV_NOSPIN=1

WORKDIR /app

# Instala o Pipenv só no estágio de build
RUN pip install --no-cache-dir pipenv==2024.4.1

COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system


FROM python:3.11-slim

    # faz os logs saírem sem buffering
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash \
    && apt-get update && apt-get install -y --no-install-recommends speedtest \
    && apt-get purge -y --auto-remove curl gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin exporter
WORKDIR /home/exporter/app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=exporter:exporter exporter.py Pipfile Pipfile.lock ./

USER exporter

EXPOSE 9798
CMD ["python", "exporter.py"]
