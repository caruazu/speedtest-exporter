"""
log_formatter.py
----------------
Formatador de logs em JSON estruturado compatível com Grafana Loki / Alloy.

Objetivos:
  - Emitir uma linha JSON por evento de log (NDJSON / JSON Lines).
  - Usar nomes de campo que o Loki e o LogQL reconhecem nativamente, permitindo
    filtrar por severity com `| json | level="error"` sem nenhuma stage de
    transformação no Alloy.
  - Incluir campos extras passados via `extra={}` no logger automaticamente.

Campos emitidos:
  ts        — timestamp ISO-8601 com fuso UTC  (Loki usa "ts" nativamente)
  level     — severity em minúsculas: debug | info | warning | error | critical
  msg       — mensagem de log
  logger    — nome do logger (ex.: "speedtest_exporter")
  caller    — arquivo:linha que originou o log
  exc       — traceback completo (somente quando há exceção)
  <extras>  — qualquer chave passada em extra={} é promovida para o nível raiz

Uso:
  from log_formatter import build_logger

  logger = build_logger("meu_app")
  logger.info("Serviço iniciado", extra={"porta": 9798})
  logger.error("Falha ao conectar", extra={"host": "db", "tentativa": 3})
"""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Campos que já existem em LogRecord e NÃO devem ser promovidos como extras
# ---------------------------------------------------------------------------
_RESERVED_LOG_RECORD_FIELDS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "taskName",
    "message",
    # campos internos adicionados pelo próprio formatador
    "ts", "level", "logger", "caller", "exc",
})


class JsonFormatter(logging.Formatter):
    """
    Formata cada LogRecord como um objeto JSON em uma única linha.

    Compatível com:
      - Grafana Loki (campo ``ts`` e ``level``)
      - Alloy loki.source.file / loki.source.docker  (zero pipeline stages)
      - LogQL  ``| json | level="error"``
      - Explore → "Detected fields" → filtro por severity no Grafana UI
    """

    # Mapa dos níveis Python → string padronizada esperada pelo Loki / Grafana
    _LEVEL_MAP: dict[int, str] = {
        logging.DEBUG:    "debug",
        logging.INFO:     "info",
        logging.WARNING:  "warning",
        logging.ERROR:    "error",
        logging.CRITICAL: "critical",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Converte um LogRecord para uma linha JSON."""

        # --- Mensagem principal (aplica % args da forma padrão do logging) ---
        record.message = record.getMessage()

        # --- Timestamp em UTC, formato RFC-3339 (ex.: 2025-04-20T13:45:00.123Z) ---
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc)
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"

        # --- Monta o payload base ---
        payload: dict[str, Any] = {
            "ts":     ts_str,
            "level":  self._LEVEL_MAP.get(record.levelno, record.levelname.lower()),
            "msg":    record.message,
            "logger": record.name,
            "caller": f"{record.filename}:{record.lineno}",
        }

        # --- Exceção (se houver) ---
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        elif record.exc_text:
            payload["exc"] = record.exc_text

        # --- Campos extras (passados via extra={} no logger) ---
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_FIELDS:
                # Garante serialização segura para tipos não-padrão
                payload[key] = _safe_value(value)

        return json.dumps(payload, ensure_ascii=False, default=str)


def _safe_value(value: Any) -> Any:
    """
    Converte valores para tipos serializáveis pelo json.dumps.
    Tipos básicos passam direto; o resto vira string.
    """
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _safe_value(v) for k, v in value.items()}
    return str(value)


def build_logger(
    name: str,
    level: str | int = logging.DEBUG,
    stream=None,
) -> logging.Logger:
    """
    Cria e retorna um logger já configurado com JsonFormatter.

    Parâmetros
    ----------
    name    : nome do logger (aparece no campo ``logger`` do JSON)
    level   : nível mínimo de log (aceita string como "DEBUG" ou constante do
              módulo logging); padrão: DEBUG
    stream  : destino do output; padrão: sys.stdout

    Exemplo
    -------
    >>> logger = build_logger("speedtest_exporter", level="INFO")
    >>> logger.info("Servidor iniciado", extra={"porta": 9798})
    {"ts":"2025-04-20T13:00:00.000Z","level":"info","msg":"Servidor iniciado",
     "logger":"speedtest_exporter","caller":"exporter.py:42","porta":9798}
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.DEBUG)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evita duplicar handlers se a função for chamada mais de uma vez
    if not logger.handlers:
        handler = logging.StreamHandler(stream or sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    # Não propaga para o root logger (evita linhas duplicadas)
    logger.propagate = False

    return logger