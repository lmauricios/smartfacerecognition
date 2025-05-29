import logging
import sys


def setup_logging(level=logging.INFO):
    """Configura o logging básico para a aplicação."""
    logger = logging.getLogger("facerec_backend")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


log = setup_logging()
