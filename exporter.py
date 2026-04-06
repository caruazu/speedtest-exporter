import time
import json
import subprocess
import os
import sys
from prometheus_client import start_http_server, Gauge

# Configurações
UPDATE_INTERVAL = int(os.getenv('SPEEDTEST_CACHE_SECONDS', 14400))
PORT = int(os.getenv('EXPORTER_PORT', 9798))

# Métricas do Prometheus
DOWNLOAD = Gauge('speedtest_download_bytes_per_second', 'Velocidade de Download (Bytes)')
UPLOAD = Gauge('speedtest_upload_bytes_per_second', 'Velocidade de Upload (Bytes)')
PING = Gauge('speedtest_ping_latency_milliseconds', 'Latencia do Ping')
JITTER = Gauge('speedtest_jitter_latency_milliseconds', 'Jitter da conexao')

def run_speedtest():
    try:
        print(f"Iniciando teste de velocidade (Intervalo: {UPDATE_INTERVAL}s)...")
        # Executa o comando oficial da Ookla
        result = subprocess.run(
            ['speedtest', '--accept-license', '--accept-gdpr', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        
        # Extrai dados crus (Bytes)
        download_bytes = data['download']['bandwidth']
        upload_bytes = data['upload']['bandwidth']
        ping = data['ping']['latency']
        jitter = data['ping']['jitter']

        # Atualiza métricas
        DOWNLOAD.set(download_bytes)
        UPLOAD.set(upload_bytes)
        PING.set(ping)
        JITTER.set(jitter)

        print(f"Sucesso: Down: {download_bytes/1024/1024:.2f} MB/s, Up: {upload_bytes/1024/1024:.2f} MB/s")

    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar speedtest: {e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"Erro geral: {e}", file=sys.stderr)

if __name__ == '__main__':
    start_http_server(PORT)
    print(f"Exporter rodando na porta {PORT}")
    
    # Executa o primeiro teste imediatamente ao iniciar
    run_speedtest()
    
    while True:
        time.sleep(UPDATE_INTERVAL)
        run_speedtest()
