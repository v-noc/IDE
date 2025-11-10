from vn_logger.logger import context_logger

class GrandParent:
    """ ID: 0aef4dcd-59eb-4b0a-82c1-dc3b71e55d22 """

    @context_logger('3dc29628-2e38-4867-8bb1-0a1aa6460292')
    def get_name(self):
        """ ID: f524bf69-3e1f-4d6d-906e-f8cdf912292b """
        pass

    @context_logger('87c6376e-34d9-449e-b29e-7675b9867aaa')
    def walk(self):
        """ ID: e3a37c00-22fd-490c-b94d-dd39e6d94859 """
        pass

    @context_logger('0eb3b811-0c9a-40f6-99c3-d0975285c1e6')
    def sleep(self):
        """ ID: dfbbacc3-b91d-4e51-8e6c-72c6f9d93f66 """
        pass

class Uncle(GrandParent):
    """ ID: e82dc2ba-b511-4096-91c2-c7f97f312c45 """

    @context_logger('e8d53c87-d9c4-468c-a6a9-ee587d26863c')
    def get_name(self):
        """ ID: 6f0276d2-c919-4e74-9f0f-16b1c008ae28 """
        pass

    @context_logger('38e05933-5526-49fb-a2c9-2b31e1de8ba4')
    def walk(self):
        """ ID: fab8038a-5741-42ce-8410-217dc4a1afc6 """
        pass

    @context_logger('a9c59927-fde1-43ae-bb7f-814b908c92ab')
    def run(self):
        """ ID: 2c33578a-b0ea-4c32-a707-ef8ee4be0fed """
        pass

class Parent(GrandParent):
    """ ID: e61d4fc3-681d-4b64-9576-deb169ce1ba1 """

    @context_logger('db07ceb7-ac05-4963-ad41-0e5f82db6cff')
    def __init__(self, name: str):
        """ ID: 321fc4ad-2dab-43e1-80f6-349c0fbeee46 """
        self.name = name

    @context_logger('ae081204-9057-42cd-b05c-869c283a9139')
    def get_name(self):
        """ ID: a2755ca0-36f8-4766-a0f2-65578edeb4ba """
        return self.name