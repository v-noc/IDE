from .core.utils.helper import create_child
from vn_logger import configure_logger, logger


@logger.context_logger('11b1c19e-faa5-44f1-836a-c1ef80d43c87')
def main():
    """ ID: 11b1c19e-faa5-44f1-836a-c1ef80d43c87 """
    child = create_child()
    logger.logger.warning("main function called")
    child.get_name()


@logger.context_logger('fb04a14a-2746-4212-8bdd-cb70779c416c')
def runner():
    """ ID: fb04a14a-2746-4212-8bdd-cb70779c416c """
    pass


if __name__ == '__main__':
    configure_logger('http://127.0.0.1:8050/api/v1/jsonrpc',
                     '86337e46-72da-4c94-8dcb-deffcd3db47c')
    print('main')
    main()
