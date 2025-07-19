from ..orm import CollectionManager
from ...models.node import Node

class NodeCollectionManager(CollectionManager[Node]):
    def __init__(self):
        super().__init__("nodes", Node)
