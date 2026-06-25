from uuid import UUID
from app.domain.base_entity import BaseEntity

def test_base_entity_auto_generates_id():
    entity = BaseEntity()
    assert isinstance(entity.id, UUID)

def test_base_entity_auto_generates_timestamps():
    entity = BaseEntity()
    assert entity.created_at is not None
    assert entity.updated_at is not None

def test_base_entity_explicit_id():
    from uuid import uuid4
    explicit_id = uuid4()
    entity = BaseEntity(id=explicit_id)
    assert entity.id == explicit_id
