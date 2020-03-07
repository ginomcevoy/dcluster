import logging


class LoggerMixin(object):
    '''
    Mixin for adding logging capabilities to a class.
    Only works on instance methods.
    '''

    @property
    def logger(self):
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)


def logger_for_me(func):
    '''
    Return a logger for the supplied function.
    '''
    name = '.'.join([
        func.__module__,
        func.__name__
    ])
    return logging.getLogger(name)
