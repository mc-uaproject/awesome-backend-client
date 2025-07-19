import logging
import sys


class CustomLogger(logging.Logger):
    def __init__(self, name: str, level: int = logging.INFO):
        super().__init__(name, level)

        formatter = logging.Formatter("%(levelname)s:     %(message)s")

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(level)

        self.addHandler(handler)


def get_logger(name: str, level: int = logging.INFO) -> CustomLogger:
    return CustomLogger(name, level)
