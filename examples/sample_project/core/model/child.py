from .parent import Parent, Uncle
from vn_logger.logger import context_logger


class Child(Parent, Uncle):
    """ ID: db9ce2c7-4a05-4b99-8dbb-0b65024446d0 """

    @context_logger('f9b3e29d-ce9e-49ea-9599-ae4ce349f326')
    def __init__(self, name: str):
        """ ID: f9b3e29d-ce9e-49ea-9599-ae4ce349f326 """
        self.name = name
        super().__init__(name)

    @context_logger('31705d6d-c950-41f5-96b5-4d2f01690c78')
    def get_name(self) -> str:
        """ ID: 31705d6d-c950-41f5-96b5-4d2f01690c78 """
        return self.name

    @context_logger('2b10cd92-9cb3-40ed-828f-b446e99bfc90')
    def set_name(self, name) -> str:
        """ ID: 2b10cd92-9cb3-40ed-828f-b446e99bfc90 """
        self.name = name

    def fly(self):
        """ ID: fc638f7e-f2a8-4fbc-8ee8-037cbb8f35c2 """
        pass
