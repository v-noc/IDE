def factory():
    """ ID: fead74f6-6c60-479f-932a-8d9122d4b708 """

    def add():
        """ ID: c4497b10-c3d2-411f-a546-e1e58ff97e55 """
        build()
        pass

    def build():
        """ ID: 8c658583-244f-41d2-aa99-da167688e0c5 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 6a561266-a739-455b-9716-588d523b321c """
    call_back_func()

def factory_call():
    """ ID: 5ea64cd4-8e8b-451b-8feb-12f48467abc5 """
    add = factory()
    add()

def curry_call():
    """ ID: bd0b40b1-172c-4906-b193-a68eb595083e """
    factory()()

def main():
    """ ID: 466ebf76-d648-440e-bdc1-a7a814e591a0 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()