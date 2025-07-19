from ..orm import CollectionManager
from ...models.project import Project

class ProjectCollectionManager(CollectionManager[Project]):
    def __init__(self):
        super().__init__("projects", Project)
