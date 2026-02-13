from app.db.woqlschema import (
    DocumentTemplate,
    EnumTemplate,
    LexicalKey,
)
from typing import Optional, Literal
from datetime import datetime


class TerminusBase(DocumentTemplate):
    """
    The base model for all TerminusDB documents.
    """
    _abstract = []
    created_at: datetime
    updated_at: datetime


class BaseSchema(TerminusBase):
    name: str
    description: str
