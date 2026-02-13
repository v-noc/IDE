from typing import Optional
from app.db.woqlschema import (
    DocumentTemplate
)
from datetime import datetime


class CodePosition(DocumentTemplate):
    """Source code location — embedded inside node documents."""
    _subdocument = []
    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int


class ThemeConfig(DocumentTemplate):
    """Theme configuration — embedded inside node documents."""
    _subdocument = []
    navbarColor: Optional[str]
    leftSidebarColor: Optional[str]
    rightSidebarColor: Optional[str]
    backgroundColor: Optional[str]
    textColor: Optional[str]
    iconColor: Optional[str]
    cardColor: Optional[str]


class DocumentSchema(DocumentTemplate):
    """Document schema — embedded inside node documents."""
    _subdocument = []
    name: str
    description: str
    data: str
    created_at: datetime
    updated_at: datetime
