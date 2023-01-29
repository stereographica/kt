import logging
import os
import sys


class Logger:
    def __init__(self) -> None:
        self.logger = logging.getLogger()
        sh = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(sh)
        self.logger.setLevel(os.getenv("LOG_LEVEL", "ERROR"))

    def get_logger(self) -> logging.Logger:
        return self.logger
