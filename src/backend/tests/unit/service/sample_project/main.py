def factory():
    """ ID: 8d59ff84-48e2-42da-ba55-4c13142bb68a """

    def add():
        """ ID: 38c65695-7809-495f-9c1f-725b392cff0e """
        build()
        pass

    def build():
        """ ID: 1a8b16b0-eea4-420a-8deb-d4428b3ec179 """
        pass
    return add


def call_back(call_back_func):
    """ ID: fe0a5343-48d7-4519-a7b8-21a5de398f7a """
    call_back_func()


def factory_call():
    """ ID: 2d7151a2-5756-4166-a041-9fd3491c2f2c """
    add = factory()
    add()


def curry_call():
    """ ID: 26cd74e0-e3a8-4304-8faa-4dd85b17a15a """
    factory()()


def main():
    """ ID: 5e8af11f-7e83-4ca5-8573-6a25b4acd165 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)


main()
