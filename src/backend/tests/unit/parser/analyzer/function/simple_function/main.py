

"""FileID: bfb2ae0c-655b-4aa0-a1e7-7a02d8e16b8b"""


def factory():
    """ID: 1ad3edb4-140e-4c42-af81-b0a75e6bd0ed"""

    def add():
        """ID: 3d4782eb-0d78-434e-9a6e-f21b27a306b3"""

        build()

    def build():
        """ID: db0744f2-0aa8-44e0-8d15-648d019494fc"""
        pass
        # build()

    return add


def call_back(call_back_func):
    """ID: 040d752e-b34b-49da-b595-c613c3e73dd4"""

    call_back_func()  # lalal


def factory_call():
    """ID: 9227c3fd-42f1-4857-8cce-472b40357e1f"""

    add = factory()
    add()


def curry_call():
    """ID: ca8cb52d-33f8-4b03-946d-7587574b69c0"""

    factory()()


def main():
    """ID: ece4c93f-b04b-4598-b4fc-147e35758f7b"""

    factory_call()
    curry_call()
    call_back(factory())


main()
