"""
log_formatter.py
----------------
Emite logs em formato logfmt, compatível nativamente com Grafana Loki / Alloy.

Campos emitidos:
  ts      — timestamp ISO-8601 UTC
  level   — debug | info | warning | error | critical
  msg     — mensagem do evento
  logger  — nome do logger
  caller  — arquivo:linha
  exc     — traceback (somente em exceções)
  <extra> — campos passados via extra={} são promovidos ao nível raiz

Uso:
  from log_formatter import build_logger
  logger = build_logger("meu_app")
  logger.info("Serviço iniciado", extra={"porta": 9798})
  # ts=2025-04-20T13:00:00.123Z level=info msg="Serviço iniciado" logger=meu_app caller=app.py:10 porta=9798
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

_LEVEL_MAP = {
    logging.DEBUG:    "debug",
    logging.INFO:     "info",
    logging.WARNING:  "warning",
    logging.ERROR:    "error",
    logging.CRITICAL: "critical",
}

_RESERVED = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message",
    "ts", "level", "logger", "caller", "exc",
})


def _quote(value: Any) -> str:
    """Formata um valor para logfmt: aspas somente quando necessário."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if not text:
        return '""'
    if any(c in text for c in (' ', '"', '=', '\n', '\r', '\t')):
        return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    return text


class LogfmtFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        ts = datetime.fromtimestamp(record.created, tz=timezone.utc)
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"

        fields = {
            "ts":     ts_str,
            "level":  _LEVEL_MAP.get(record.levelno, record.levelname.lower()),
            "msg":    record.message,
            "logger": record.name,
            "caller": f"{record.filename}:{record.lineno}",
        }

        if record.exc_info:
            fields["exc"] = self.formatException(record.exc_info)
        elif record.exc_text:
            fields["exc"] = record.exc_text

        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                fields[key] = value

        fixed = ("ts", "level", "msg", "logger", "caller")
        parts = [f"{k}={_quote(fields[k])}" for k in fixed if k in fields]
        parts += [f"{k}={_quote(v)}" for k, v in sorted(fields.items()) if k not in fixed]

        return " ".join(parts)


def build_logger(name: str, level: str | int = logging.DEBUG, stream=None) -> logging.Logger:
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.DEBUG)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(stream or sys.stdout)
        handler.setFormatter(LogfmtFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger
