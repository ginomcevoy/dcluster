import logging


class LoggerMixin(object):

    @property
    def logger(self):
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)


def logger_for_me(func):
    name = '.'.join([
        func.__module__,
        func.__name__
    ])
    return logging.getLogger(name)
