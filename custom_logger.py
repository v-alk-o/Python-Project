import logging


class CustomLogger:
	def get_logger(level="INFO"):
		logger = logging.getLogger(CustomLogger.__name__)
		loggingLevel = logging.getLevelName(level)
		logger.setLevel(loggingLevel)
		formatter = logging.Formatter("[%(asctime)s]  %(levelname)-8s  %(message)s")
		streamHandler = logging.StreamHandler()
		streamHandler.setFormatter(formatter)
		logger.addHandler(streamHandler)
		return logger