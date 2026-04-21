# Speedtest Exporter

Exporter Prometheus para o binário oficial da [Ookla Speedtest CLI](https://www.speedtest.net/apps/cli), com metricas e logs prontos para consumo pelo **Grafana Loki** via **Alloy**

---

## Métricas expostas

| Métrica | Tipo | Descrição |
|---|---|---|
| `speedtest_download_bytes_per_second` | Gauge | Velocidade de download em bytes/s |
| `speedtest_upload_bytes_per_second` | Gauge | Velocidade de upload em bytes/s |
| `speedtest_ping_latency_milliseconds` | Gauge | Latência de ping em ms |
| `speedtest_jitter_latency_milliseconds` | Gauge | Jitter da conexão em ms |

Endpoint de métricas: `http://localhost:9798/metrics`

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `EXPORTER_PORT` | `9798` | Porta do servidor de métricas |
| `SPEEDTEST_CACHE_SECONDS` | `14400` | Intervalo entre testes (em segundos) |
| `LOG_LEVEL` | `DEBUG` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Executando

### Docker (recomendado)

```bash
docker run -d \
  --name speedtest-exporter \
  -p 9798:9798 \
  -e LOG_LEVEL=DEBUG \
  -e SPEEDTEST_CACHE_SECONDS=3600 \
  caruazu/speedtest-exporter:latest
```

### Docker Compose

```yaml
services:
  speedtest-exporter:
    image: caruazu/speedtest-exporter:latest
    container_name: speedtest-exporter
    restart: unless-stopped
    ports:
      - "9798:9798"
    environment:
      LOG_LEVEL: DEBUG
      SPEEDTEST_CACHE_SECONDS: 3600
```

