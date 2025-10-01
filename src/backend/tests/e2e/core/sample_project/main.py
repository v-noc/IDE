from .core.utils.helper import create_child


def main():
    child = create_child()
    print(child.get_name())


if __name__ == "__main__":
    main()
