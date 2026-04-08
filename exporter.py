import time
import json
import subprocess
import os
import sys
import logging
from prometheus_client import start_http_server, Gauge

# Configurações
UPDATE_INTERVAL = int(os.getenv('SPEEDTEST_CACHE_SECONDS', 14400))
PORT = int(os.getenv('EXPORTER_PORT', 9798))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()

# Configuração de logs
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='[%(name)s] %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger('speedtest_exporter')

# Métricas do Prometheus
DOWNLOAD = Gauge('speedtest_download_bytes_per_second', 'Velocidade de Download (Bytes)')
UPLOAD = Gauge('speedtest_upload_bytes_per_second', 'Velocidade de Upload (Bytes)')
PING = Gauge('speedtest_ping_latency_milliseconds', 'Latencia do Ping')
JITTER = Gauge('speedtest_jitter_latency_milliseconds', 'Jitter da conexao')


def run_speedtest():
    logger.info('Iniciando teste de velocidade', extra=None)
    try:
        logger.debug('Executando comando speedtest')
        result = subprocess.run(
            ['speedtest', '--accept-license', '--accept-gdpr', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug('Comando speedtest executado com sucesso')

        data = json.loads(result.stdout)
        logger.debug('Resposta JSON carregada com sucesso')

        # Extrai dados crus (Bytes)
        download_bytes = data['download']['bandwidth']
        upload_bytes = data['upload']['bandwidth']
        ping = data['ping']['latency']
        jitter = data['ping']['jitter']

        logger.info(
            'Resultado do speedtest: download=%s B/s upload=%s B/s ping=%s ms jitter=%s ms',
            download_bytes,
            upload_bytes,
            ping,
            jitter,
        )

        # Atualiza métricas
        DOWNLOAD.set(download_bytes)
        UPLOAD.set(upload_bytes)
        PING.set(ping)
        JITTER.set(jitter)

        logger.info(
            'Metricas atualizadas com sucesso: down=%.2f MB/s up=%.2f MB/s',
            download_bytes / 1024 / 1024,
            upload_bytes / 1024 / 1024,
        )

    except subprocess.CalledProcessError as e:
        logger.error('Erro ao executar speedtest: %s', e.stderr.strip() if e.stderr else str(e))
    except json.JSONDecodeError as e:
        logger.exception('Falha ao interpretar JSON retornado pelo speedtest: %s', e)
    except KeyError as e:
        logger.exception('Campo esperado nao encontrado no resultado do speedtest: %s', e)
    except Exception:
        logger.exception('Erro geral durante a execucao do speedtest')


if __name__ == '__main__':
    logger.info(
        'Inicializando exporter com configuracoes: porta=%s intervalo=%ss nivel_log=%s',
        PORT,
        UPDATE_INTERVAL,
        LOG_LEVEL,
    )
    start_http_server(PORT)
    logger.info('Exporter rodando na porta %s', PORT)

    # Executa o primeiro teste imediatamente ao iniciar
    run_speedtest()

    while True:
        logger.debug('Aguardando %s segundos para o proximo teste', UPDATE_INTERVAL)
        time.sleep(UPDATE_INTERVAL)
        run_speedtest()
