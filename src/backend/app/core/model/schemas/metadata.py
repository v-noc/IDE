from typing import Optional
from app.db.woqlschema import (
    DocumentTemplate
)
from datetime import datetime

from app.core.model.properties import CodePosition, ThemeConfig


class CodePositionSchema(DocumentTemplate):
    """Source code location — embedded inside node documents."""
    _subdocument = []
    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int

    @staticmethod
    def from_pydantic(code_position: CodePosition):
        return CodePositionSchema(
            line_no=code_position.line_no,
            col_offset=code_position.col_offset,
            end_line_no=code_position.end_line_no,
            end_col_offset=code_position.end_col_offset,
        )

    def to_pydantic(self):
        return CodePosition(
            line_no=self.line_no,
            col_offset=self.col_offset,
            end_line_no=self.end_line_no,
            end_col_offset=self.end_col_offset,
        )


class ThemeConfigSchema(DocumentTemplate):
    """Theme configuration — embedded inside node documents."""
    _subdocument = []
    navbarColor: Optional[str]
    leftSidebarColor: Optional[str]
    rightSidebarColor: Optional[str]
    backgroundColor: Optional[str]
    textColor: Optional[str]
    iconColor: Optional[str]
    cardColor: Optional[str]

    @staticmethod
    def from_pydantic(theme_config: ThemeConfig):
        if theme_config is None:
            return None
        return ThemeConfigSchema(
            navbarColor=theme_config.navbarColor,
            leftSidebarColor=theme_config.leftSidebarColor,
            rightSidebarColor=theme_config.rightSidebarColor,
            backgroundColor=theme_config.backgroundColor,
            textColor=theme_config.textColor,
            iconColor=theme_config.iconColor,
            cardColor=theme_config.cardColor,
        )

    def to_pydantic(self):
        return ThemeConfig(
            navbarColor=self.navbarColor,
            leftSidebarColor=self.leftSidebarColor,
            rightSidebarColor=self.rightSidebarColor,
            backgroundColor=self.backgroundColor,
            textColor=self.textColor,
            iconColor=self.iconColor,
            cardColor=self.cardColor,
        )


class DocumentSchema(DocumentTemplate):
    """Document schema — embedded inside node documents."""
    _subdocument = []
    name: str
    description: str
    data: str
    created_at: datetime
    updated_at: datetime
