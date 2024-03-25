import logging
import os


class AppLogger:
    _instance = None

    @staticmethod
    def get_instance():
        if AppLogger._instance is None:
            AppLogger._instance = AppLogger._create_logger()
        return AppLogger._instance

    @staticmethod
    def _create_logger():
        logger = logging.getLogger("common_logger")
        logger.setLevel(logging.INFO)
        log_file = "gemini_app.log"
        if not os.path.exists(log_file):
            with open(log_file, "w") as file:
                file.write("The logs for Gemini Hackathon will be printed here\n")

        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(logging.StreamHandler())
        return logger
