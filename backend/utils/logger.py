"""
Sistema de logging estruturado em JSON com rotação de arquivos.
"""
import logging
import os
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON customizado com campos extras."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'tool_name'):
            log_record['tool_name'] = record.tool_name


def setup_logger(name: str, debug: bool = False) -> logging.Logger:
    """
    Configura logger estruturado em JSON.

    Logs vão para:
    - Console: formato JSON
    - Arquivo logs/app.log: todos os níveis (rotação 10MB)
    - Arquivo logs/error.log: apenas erros (rotação 10MB)

    Args:
        name: Nome do logger (geralmente __name__)
        debug: Se True, habilita nível DEBUG

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    if logger.handlers:
        return logger

    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    log_dir = os.getenv("LOG_DIR", "./logs")
    os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        f"{log_dir}/app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    error_handler = RotatingFileHandler(
        f"{log_dir}/error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    logger.addHandler(error_handler)

    return logger
