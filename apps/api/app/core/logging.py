import logging
import logging.config

from app.core.config import settings


def setup_logging() -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": ("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": settings.LOG_LEVEL,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
        },
    }

    logging.config.dictConfig(logging_config)
