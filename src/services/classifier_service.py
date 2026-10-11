from typing import Any, List, Optional, Sequence, cast

from src.core.errors import BusinessRuleError, ConflictError, NotFoundError

from src.models.classifiers import DocumentClassifier, HoClassifier, ItemClassifier, SxdClassifier
from src.repository.classifier_repository import (
    DocumentClassifierRepository,
    HoClassifierRepository,
    ItemClassifierRepository,
    SxdClassifierRepository,
)
from src.schemas.classifiers import (
    DocumentClassifierCreate,
    DocumentClassifierUpdate,
    HoClassifierCreate,
    HoClassifierTree,
    HoClassifierUpdate,
    ItemClassifierCreate,
    ItemClassifierUpdate,
    SxdClassifierCreate,
    SxdClassifierUpdate,
)


def ensure_no_cycle(repo: Any, obj_id: int, new_parent_id: Optional[int]) -> None:
    """Смена родителя не должна создавать цикл: новый родитель не может быть самим узлом или его потомком."""
    if new_parent_id is None:
        return
    if repo.get_by_id(new_parent_id) is None:
        raise NotFoundError(f"Родительский класс {new_parent_id} не найден")
    current: Optional[int] = new_parent_id
    seen: set[int] = set()
    while current is not None and current not in seen:
        if current == obj_id:
            raise BusinessRuleError("Смена родителя создаёт цикл в классификаторе")
        seen.add(current)
        node = repo.get_by_id(current)
        current = node.parent_id if node else None


class SxdClassifierService:
    def __init__(self, repo: SxdClassifierRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[SxdClassifier]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> SxdClassifier:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("SxdClassifier not found")
        return obj

    def create(self, data: SxdClassifierCreate) -> SxdClassifier:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: SxdClassifierUpdate) -> SxdClassifier:
        obj = self.get_by_id(obj_id)
        ensure_no_cycle(self.repo, obj_id, getattr(data, "parent_id", None))
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class HoClassifierService:
    def __init__(self, repo: HoClassifierRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[HoClassifier]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> HoClassifier:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("HoClassifier not found")
        return obj

    def create(self, data: HoClassifierCreate) -> HoClassifier:
        if self.repo.get_by_code(data.code):
            raise ConflictError(f"HoClassifier '{data.code}' exists")
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: HoClassifierUpdate) -> HoClassifier:
        obj = self.get_by_id(obj_id)
        ensure_no_cycle(self.repo, obj_id, getattr(data, "parent_id", None))
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)

    def get_tree(self) -> List[HoClassifierTree]:
        """Строит дерево классификатора из плоского списка."""
        all_nodes = self.repo.get_all(limit=10000)
        node_map: dict[int, HoClassifierTree] = {
            cast(int, n.id): HoClassifierTree(id=cast(int, n.id), parent_id=n.parent_id, name=n.name, code=n.code)
            for n in all_nodes
            if n.id is not None
        }
        roots: List[HoClassifierTree] = []
        for node in node_map.values():
            if node.parent_id and node.parent_id in node_map:
                node_map[node.parent_id].children.append(node)
            else:
                roots.append(node)
        return roots


class DocumentClassifierService:
    def __init__(self, repo: DocumentClassifierRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[DocumentClassifier]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> DocumentClassifier:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("DocumentClassifier not found")
        return obj

    def create(self, data: DocumentClassifierCreate) -> DocumentClassifier:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: DocumentClassifierUpdate) -> DocumentClassifier:
        obj = self.get_by_id(obj_id)
        ensure_no_cycle(self.repo, obj_id, getattr(data, "parent_id", None))
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class ItemClassifierService:
    def __init__(self, repo: ItemClassifierRepository) -> None:
        self.repo = repo

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ItemClassifier]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> ItemClassifier:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("ItemClassifier not found")
        return obj

    def create(self, data: ItemClassifierCreate) -> ItemClassifier:
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: ItemClassifierUpdate) -> ItemClassifier:
        obj = self.get_by_id(obj_id)
        ensure_no_cycle(self.repo, obj_id, getattr(data, "parent_id", None))
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
