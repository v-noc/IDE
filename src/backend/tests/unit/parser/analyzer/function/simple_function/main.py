def factory():
    """ID: b084632a-da24-418f-a0ae-367c8d14317a"""
    def add():
        """ID: a2259dcd-9c30-42ad-95ca-c3d3e22d7fc3"""
        build()
        pass

    def build():
        """ID: 624f6ea5-526b-4215-a7e8-57a334161334"""
        pass
    return add


def call_back(call_back_func):
    """ID: ca63242a-af2c-459b-a91f-4d2223bae1c0"""

    call_back_func()  # lalal


def factory_call():
    """ID: 1d6f22ca-4a11-4a01-ae07-c8d487da97bf"""
    add = factory()
    add()


def curry_call():
    """ID: abb5d210-feb7-4c60-a061-265d8ab172e2"""
    factory()()


def main():
    """ID: 34a79751-8aad-40a6-9ca6-64e610fa230e"""
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)


main()
