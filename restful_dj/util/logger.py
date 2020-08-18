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
        # noinspection PyUnresolvedReferences
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
    temp = message if e is None else '%s\n\t%s' % (message, repr(e))

    # 非开发模式时，始终不会输出堆栈信息
    if not settings.DEBUG:
        log('ERROR', temp, e)
        return

    # print('\033[1;31;47m {0} \033[0m'.format(temp))
    # if e is not None:
    #     print(repr(e.__traceback__.tb_frame))

    # 不需要抛出异常
    if not _raise:
        log('ERROR', temp, e)
        return

    # 抛出新的异常
    if e is None:
        raise Exception(message)

    # 修改异常消息
    new_msg = '%s\n\t%s' % (message, e.args[0]) if len(e.args) > 0 else message
    e.args = (new_msg,)
    raise e
