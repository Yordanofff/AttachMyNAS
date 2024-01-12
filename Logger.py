import logging


class MyLogger:
    def __init__(self, prefix: str, log_file='app.log', log_level=logging.INFO):
        self.log_file = log_file
        self.log_level = log_level
        self.prefix = prefix

        logging.basicConfig(
            level=self.log_level,
            filename=self.log_file,
            filemode='a',
            format=f'%(asctime)s [%(levelname)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def debug(self, message):
        logging.debug(f"[{self.prefix}]: {message}")

    def info(self, message):
        logging.info(f"[{self.prefix}]: {message}")

    def warning(self, message):
        logging.warning(f"[{self.prefix}]: {message}")

    def error(self, message):
        logging.error(f"[{self.prefix}]: {message}")

    def critical(self, message):
        logging.critical(f"[{self.prefix}]: {message}")
