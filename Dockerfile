FROM python:3.11-slim

# Variáveis de ambiente para evitar buffer no log
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 1. Instalar dependências básicas e o Speedtest CLI Oficial da Ookla
# o endereço é do .sh encontrado em https://www.speedtest.net/pt/apps/cli
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg1 \
    apt-transport-https \
    dirmngr \
    lsb-release \
    && curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash \
    && apt-get install -y --no-install-recommends speedtest \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar biblioteca do Prometheus para Python
RUN pip install --no-cache-dir prometheus-client==0.22.0

# 3. Configuração de Usuário Não-Root (Segurança)
# Criamos um usuário 'exporter' para não rodar como root
RUN useradd --create-home --shell /usr/sbin/nologin exporter
USER exporter
WORKDIR /home/exporter

# 4. Copiar nosso script
COPY --chown=exporter:exporter exporter.py .

# 5. Comando de execução
EXPOSE 9798
CMD ["python", "exporter.py"]
