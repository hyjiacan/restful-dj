from django.conf import settings

CUSTOMIZE_LOGGER = None


def set_logger(logger):
    """
    设置自定义的 logger
    :param logger:
    :return:
    """
    global CUSTOMIZE_LOGGER
    CUSTOMIZE_LOGGER = logger


def log(level, message, e=None):
    if CUSTOMIZE_LOGGER is None:
        print('[%s] %s' % (level, message))
    else:
        CUSTOMIZE_LOGGER.log(level, message, e)


def debug(message):
    log('debug', message)


def success(message):
    log('success', message)


def info(message):
    log('info', message)


def warning(message):
    log('warning', message)


def error(message, e=None, _raise=True):
    temp = message if e is None else '%s: %s' % (message, repr(e))
    if settings.DEBUG:
        print('\033[1;31;47m {0} \033[0m'.format(temp))
        if e is not None:
            print(repr(e.__traceback__.tb_frame))
        if _raise:
            raise Exception(message)
    log('ERROR', temp, e)
