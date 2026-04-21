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
  -e LOG_LEVEL=INFO \
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
      LOG_LEVEL: INFO
      SPEEDTEST_CACHE_SECONDS: 3600
```

## Logs JSON estruturados

Todos os logs são emitidos em formato **JSON Lines (NDJSON)** — uma linha JSON por evento — compatíveis nativamente com Grafana Loki e Alloy.

```json
{"ts":"2025-04-20T13:00:00.123Z","level":"info","msg":"Resultado do speedtest","logger":"speedtest_exporter","caller":"exporter.py:47","download_bytes_per_sec":98765432,"upload_bytes_per_sec":45678901,"ping_ms":12.3,"jitter_ms":0.8}
{"ts":"2025-04-20T13:00:00.130Z","level":"info","msg":"Metricas atualizadas com sucesso","logger":"speedtest_exporter","caller":"exporter.py:57","download_mbps":94.18,"upload_mbps":43.59}
```

### Campos do log

| Campo | Exemplo | Descrição |
|---|---|---|
| `ts` | `2025-04-20T13:00:00.123Z` | Timestamp UTC (RFC-3339) |
| `level` | `info` | Severity: `debug` \| `info` \| `warning` \| `error` \| `critical` |
| `msg` | `"Resultado do speedtest"` | Mensagem do evento |
| `logger` | `speedtest_exporter` | Nome do logger |
| `caller` | `exporter.py:47` | Arquivo e linha de origem |
| `exc` | _traceback_ | Presente apenas em exceções |
| `<extras>` | `download_mbps`, `porta`… | Campos contextuais do evento |

### Queries LogQL no Grafana

Por usar campos padronizados, é possível filtrar logs diretamente sem nenhuma configuração extra no Alloy:

```logql
# Apenas erros
{job="speedtest"} | json | level="error"

# Resultados de teste com download abaixo de 50 Mbps
{job="speedtest"} | json | msg="Resultado do speedtest" | download_mbps < 50

# Série temporal de latência a partir dos logs
{job="speedtest"} | json | unwrap ping_ms | rate[5m]
```

---
