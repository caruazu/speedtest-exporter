import json
import os
import subprocess
import time

from prometheus_client import start_http_server, Gauge

from log_formatter import build_logger

# Configurações
UPDATE_INTERVAL = int(os.getenv('SPEEDTEST_CACHE_SECONDS', 14400))
PORT = int(os.getenv('EXPORTER_PORT', 9798))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()

# Logger logfmt estruturado — compatível com Grafana Loki / Alloy
logger = build_logger('speedtest_exporter', level=LOG_LEVEL)

# Métricas do Prometheus
DOWNLOAD = Gauge('speedtest_download_bytes_per_second', 'Velocidade de Download (Bytes)')
UPLOAD   = Gauge('speedtest_upload_bytes_per_second',   'Velocidade de Upload (Bytes)')
PING     = Gauge('speedtest_ping_latency_milliseconds', 'Latencia do Ping')
JITTER   = Gauge('speedtest_jitter_latency_milliseconds', 'Jitter da conexao')


def run_speedtest():
    logger.info('Iniciando teste de velocidade')
    try:
        logger.debug('Executando comando speedtest')
        result = subprocess.run(
            ['speedtest', '--accept-license', '--accept-gdpr', '--format=json'],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)

        download_bytes = data['download']['bandwidth']
        upload_bytes   = data['upload']['bandwidth']
        ping           = data['ping']['latency']
        jitter         = data['ping']['jitter']

        DOWNLOAD.set(download_bytes)
        UPLOAD.set(upload_bytes)
        PING.set(ping)
        JITTER.set(jitter)

        logger.info(
            'Metricas atualizadas',
            extra={
                'download_mbps': round(download_bytes / 1024 / 1024, 2),
                'upload_mbps':   round(upload_bytes   / 1024 / 1024, 2),
                'ping_ms':       ping,
                'jitter_ms':     jitter,
            },
        )

    except subprocess.CalledProcessError as e:
        logger.error(
            'Erro ao executar speedtest',
            extra={'stderr': e.stderr.strip() if e.stderr else str(e)},
        )
    except json.JSONDecodeError:
        logger.exception('Falha ao interpretar JSON retornado pelo speedtest')
    except KeyError as e:
        logger.exception('Campo esperado nao encontrado no resultado do speedtest', extra={'campo': str(e)})
    except Exception:
        logger.exception('Erro inesperado durante a execucao do speedtest')


if __name__ == '__main__':
    logger.info(
        'Inicializando exporter',
        extra={
            'porta':       PORT,
            'intervalo_s': UPDATE_INTERVAL,
            'nivel_log':   LOG_LEVEL,
        },
    )
    start_http_server(PORT)
    logger.info('Exporter rodando', extra={'porta': PORT})

    run_speedtest()

    while True:
        logger.debug('Aguardando proximo teste', extra={'intervalo_s': UPDATE_INTERVAL})
        time.sleep(UPDATE_INTERVAL)
        run_speedtest()