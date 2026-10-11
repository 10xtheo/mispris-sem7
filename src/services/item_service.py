from typing import Optional, Sequence

from src.core.errors import BusinessRuleError, ConflictError, NotFoundError

from src.models.items import Item, ItemBatch, UnitQuantity
from src.repository.bom_repository import ItemBomRepository
from src.repository.enum_repository import EnumTypeRepository, EnumValueRepository
from src.repository.item_repository import ItemBatchRepository, ItemRepository, UnitQuantityRepository
from src.schemas.items import ItemBatchCreate, ItemCreate, ItemUpdate, UnitQuantityCreate


class ItemService:
    def __init__(
        self,
        repo: ItemRepository,
        enum_values: Optional[EnumValueRepository] = None,
        enum_types: Optional[EnumTypeRepository] = None,
        boms: Optional[ItemBomRepository] = None,
    ) -> None:
        self.repo = repo
        self.enum_values = enum_values
        self.enum_types = enum_types
        self.boms = boms

    def _check_item_type(self, item_type_id: Optional[int]) -> Optional[str]:
        """Тип изделия должен быть значением перечисления 'item_type'. Возвращает код типа."""
        if item_type_id is None or self.enum_values is None or self.enum_types is None:
            return None
        ev = self.enum_values.get_by_id(item_type_id)
        et = self.enum_types.get_by_code("item_type")
        if not ev or not et or ev.enum_type_id != et.id:
            raise BusinessRuleError(f"Значение {item_type_id} не является типом изделия (перечисление item_type)")
        return ev.code

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Item]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, obj_id: int) -> Item:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("Item not found")
        return obj

    def search(self, name: str) -> Sequence[Item]:
        return self.repo.search_by_name(name)

    def create(self, data: ItemCreate) -> Item:
        if self.repo.get_by_number(data.number):
            raise ConflictError(f"Item with number '{data.number}' exists")
        self._check_item_type(data.item_type_id)
        return self.repo.create(data.model_dump())

    def update(self, obj_id: int, data: ItemUpdate) -> Item:
        obj = self.get_by_id(obj_id)
        if data.number and data.number != obj.number and self.repo.get_by_number(data.number):
            raise ConflictError(f"Item with number '{data.number}' exists")
        type_code = self._check_item_type(data.item_type_id)
        if type_code == "material" and self.boms is not None and self.boms.count_own_active(obj_id) > 0:
            raise BusinessRuleError("Нельзя сделать изделие материалом: у него есть спецификация")
        return self.repo.update(obj, data.model_dump(exclude_none=True))

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class UnitQuantityService:
    def __init__(self, repo: UnitQuantityRepository) -> None:
        self.repo = repo

    def get_by_item(self, item_id: int) -> Sequence[UnitQuantity]:
        return self.repo.get_by_item(item_id)

    def get_by_id(self, obj_id: int) -> UnitQuantity:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("UnitQuantity not found")
        return obj

    def create(self, data: UnitQuantityCreate) -> UnitQuantity:
        if data.coefficient <= 0:
            raise BusinessRuleError("Коэффициент пересчёта ЕИ должен быть больше нуля")
        if data.is_base and self.repo.get_base_unit(data.item_id):
            raise ConflictError("У изделия уже есть базовая ЕИ количества")
        return self.repo.create(data.model_dump())

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)


class ItemBatchService:
    def __init__(self, repo: ItemBatchRepository) -> None:
        self.repo = repo

    def get_by_item(self, item_id: int) -> Sequence[ItemBatch]:
        return self.repo.get_by_item(item_id)

    def get_by_id(self, obj_id: int) -> ItemBatch:
        obj = self.repo.get_by_id(obj_id)
        if not obj:
            raise NotFoundError("ItemBatch not found")
        return obj

    def create(self, data: ItemBatchCreate) -> ItemBatch:
        return self.repo.create(data.model_dump())

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        self.repo.delete(obj)
