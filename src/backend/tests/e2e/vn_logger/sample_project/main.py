def factory():
    """ ID: 041956c2-0c4e-4d1b-a3d4-cb7928204db2 """

    def add():
        """ ID: a4e82d35-5437-4313-afe3-8554317bdb7b """
        build()
        pass

    def build():
        """ ID: 27ba0419-a167-4b52-8559-43489d256068 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 86fee55d-8ad4-41a1-bd0e-8eea9cd1dd06 """
    call_back_func()

def factory_call():
    """ ID: d51a3b64-4cd1-4440-9364-51f762b57f65 """
    add = factory()
    add()

def curry_call():
    """ ID: 10cd3335-705f-4472-88f0-550626105a43 """
    factory()()

def main():
    """ ID: c34f5cfa-9136-444d-8b69-64a0f193ab3a """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()