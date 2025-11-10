from ..model.child import Child
from vn_logger.logger import context_logger, logger


@context_logger('1a5b7f13-911d-450a-ad84-3ffe6b577edd')
def create_child():
    """ ID: 1a5b7f13-911d-450a-ad84-3ffe6b577edd """
    child = Child('whhat')
    child.name = "what the fuck"
    logger.error('Child created failed')
    return child
