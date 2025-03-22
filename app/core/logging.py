import logging
import logging.config


logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "myapp": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


def get_logger(name: str) -> logging.Logger:
    logging.config.dictConfig(logging_config)
    return logging.getLogger(name)
