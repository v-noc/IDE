from .core.utils.helper import create_child


def main():
    child = create_child()
    child.get_name()


def runner():
    pass


if __name__ == '__main__':
    print('main')
    main()
